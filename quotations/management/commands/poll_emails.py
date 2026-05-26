"""
Management command: python manage.py poll_emails

Connects to each active TeamEmailConfig inbox via IMAP, fetches UNSEEN messages,
classifies them, and creates Leads for genuine product inquiries.
"""
import email
import imaplib
import re
from email.header import decode_header
from datetime import timedelta

from django.core.management.base import BaseCommand

from django.utils import timezone

from quotations.models import Lead, Quotation, TeamEmailConfig, MarketOrder
from database.models import Broker
from quotations.services.llm import classify_message, classify_broker_response

# Senders we never want to create leads from
SPAM_PATTERNS = re.compile(
    r'no.?reply|noreply|newsletter|unsubscribe|donotreply|mailer-daemon|postmaster',
    re.IGNORECASE,
)

_HEADER_LINE_RE = re.compile(r'^(?:from|to|cc|date|sent|subject)\s*:', re.IGNORECASE)
_SEPARATOR_LINE_RE = re.compile(r'^[-_=]{3,}')


def _strip_reply_chain(text: str) -> str:
    """
    Keep only the newest message in an email thread.

    Handles:
      - -----Original Message----- (Outlook)
      - __________ separator lines (Outlook)
      - On [date], Name wrote:  (single-line Gmail / most clients)
      - On [date], Name\\n<email> wrote:  (two-line Gmail wrap)
      - From: X / Sent: Y blocks in reply chains (Outlook inline replies)
      - > quoted lines (plain-text quoting)

    NOTE: From:/Date: blocks at the START of the body (forward wrappers, e.g.
    "--------- Forwarded message ---------") are intentionally NOT treated as
    cut points — the forwarded content is the actual inquiry.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.splitlines()

    cutoff = len(lines)
    # Count non-blank, non-header, non-separator lines seen so far.
    # We only apply From/Sent cuts once real content has appeared, so that
    # forward wrappers at the top of the body are not mistakenly stripped.
    content_seen = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Track real content lines (not blank, not email headers, not separators)
        if line and not _HEADER_LINE_RE.match(line) and not _SEPARATOR_LINE_RE.match(line):
            content_seen += 1

        # -----Original Message----- (Outlook) — always a hard cut
        if re.match(r'-{3,}.*original\s+message', line, re.IGNORECASE):
            cutoff = i
            break

        # --------- Forwarded message --------- (Gmail) — cut only after real content;
        # at position 0 it's the outer wrapper we want to keep, nested = old chain
        if re.match(r'-{3,}.*forwarded\s+message', line, re.IGNORECASE) and content_seen > 0:
            cutoff = i
            break

        # __________ separator — only cut once real content has been seen
        if re.match(r'_{5,}\s*$', line) and content_seen > 0:
            cutoff = i
            break

        # "On [date/info] wrote:" — single line or two-line Gmail wrap
        if re.match(r'on\s+', line, re.IGNORECASE):
            if re.search(r'\bwrote\s*:\s*$', line, re.IGNORECASE):
                cutoff = i
                break
            next_line = lines[i + 1].strip() if i + 1 < len(lines) else ''
            if next_line and re.search(r'\bwrote\s*:\s*$', next_line, re.IGNORECASE):
                cutoff = i
                break

        # From: X / Sent: Y inline reply block — only cut once enough real
        # content has appeared (avoids cutting on forward-wrapper headers).
        # Look ahead past blank lines: Outlook often inserts a blank between From: and Sent:.
        if re.match(r'from\s*:', line, re.IGNORECASE) and content_seen >= 3:
            found_reply_header = False
            for look in range(i + 1, min(i + 5, len(lines))):
                peeked = lines[look].strip()
                if not peeked:
                    continue  # skip blank lines
                if re.match(r'(?:sent|date|to)\s*:', peeked, re.IGNORECASE):
                    found_reply_header = True
                break  # first non-blank line settles it
            if found_reply_header:
                cutoff = i
                break

        i += 1

    result = [l for l in lines[:cutoff] if not l.lstrip().startswith('>')]
    return '\n'.join(result).strip()


def _decode(value, charset=None):
    """Decode an encoded email header value to a plain string."""
    if isinstance(value, bytes):
        return value.decode(charset or 'utf-8', errors='replace')
    return value or ''


def _parse_plain_body(msg):
    """Extract plain-text body from an email.message.Message object."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and not part.get('Content-Disposition'):
                charset = part.get_content_charset() or 'utf-8'
                return _decode(part.get_payload(decode=True), charset)
    else:
        charset = msg.get_content_charset() or 'utf-8'
        return _decode(msg.get_payload(decode=True), charset)
    return ''


def _parse_sender(from_header):
    """Return (name, email) from a From header string."""
    name, addr = email.utils.parseaddr(from_header or '')
    parts = decode_header(name)
    name = ''.join(_decode(part, enc) for part, enc in parts).strip()
    return name, addr.lower()

def _find_broker(email_addr: str):
    """Return the active Broker whose email matches sender, or None."""
    if not email_addr:
        return None
    return Broker.objects.filter(email__iexact=email_addr, is_active=True).first()


class Command(BaseCommand):
    help = 'Poll active team email inboxes and create Leads for product inquiries.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Classify and print results without creating Leads or marking emails as seen.',
        )
        parser.add_argument(
            '--scheduled',
            action='store_true',
            help='Skip inboxes that were polled within their configured interval'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        scheduled = options['scheduled']
        configs = TeamEmailConfig.objects.filter(is_active=True)

        if not configs.exists():
            self.stdout.write(self.style.WARNING('No active TeamEmailConfig found. Nothing to do.'))
            return

        for config in configs:
            if scheduled and config.last_polled_at:
                due_at = config.last_polled_at + timedelta(minutes=config.poll_interval_minutes)
                if timezone.now() < due_at:
                    self.stdout.write(f'  [SKIP-TIMER]   {config} — next poll at {due_at.strftime("%H:%M:%S")}')
                    continue

            self.stdout.write(f'\n── {config} ──')
            try:
                self._poll(config, dry_run)
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'  ERROR: {exc}'))

    def _poll(self, config, dry_run):
        if config.use_ssl:
            imap = imaplib.IMAP4_SSL(config.imap_host, config.imap_port)
        else:
            imap = imaplib.IMAP4(config.imap_host, config.imap_port)

        imap.login(config.imap_username, config.imap_password)
        imap.select('INBOX')

        _, data = imap.search(None, 'UNSEEN')
        msg_ids = data[0].split()

        if not msg_ids:
            self.stdout.write('  No new messages.')
            imap.logout()
            return

        self.stdout.write(f'  {len(msg_ids)} unseen message(s).')

        for msg_id in msg_ids:
            _, raw = imap.fetch(msg_id, '(BODY.PEEK[])')
            msg = email.message_from_bytes(raw[0][1])

            subject_parts = decode_header(msg.get('Subject', ''))
            subject = ''.join(_decode(p, enc) for p, enc in subject_parts).strip()
            sender_name, sender_email = _parse_sender(msg.get('From', ''))
            raw_body = _parse_plain_body(msg).strip()
            body = _strip_reply_chain(raw_body)

            # ── Pre-filter: skip automated senders ───────────────────────────
            if SPAM_PATTERNS.search(sender_email):
                self.stdout.write(f'  [SKIP-SPAM]    {sender_email}')
                if not dry_run:
                    imap.store(msg_id, '+FLAGS', '\\Seen')
                continue

            # -- Handle broker replies -----------------------------------------
            broker = _find_broker(sender_email)
            if broker: 
                open_order = MarketOrder.objects.filter(
                    broker=broker,
                    status='rate_sent',
                ).order_by('-created_at').first()

                if open_order:
                    response_type = classify_broker_response(body)
                    stamp = timezone.now().strftime('%d %b %Y %H:%M')
                    block = (
                        f'\n\n--- Broker reply ({response_type}) on {stamp} ---\n'
                        f'{body.strip()}'
                    )
                    if not dry_run:
                        if open_order.lead:
                            open_order.lead.notes = (open_order.lead.notes or '') + block
                            open_order.lead.save(update_fields=['notes'])

                        if response_type == 'confirmation':
                            open_order.status = 'broker_confirmed'
                            open_order.broker_confirmed_at = timezone.now()
                            open_order.save(update_fields=['status', 'broker_confirmed_at'])

                    if response_type == 'confirmation':
                        self.stdout.write(self.style.SUCCESS(
                            f'  [BROKER-CONFIRM] {broker.name} → MO-{open_order.pk:05d}'
                        ))
                    else:
                        self.stdout.write(
                            f'  [BROKER-COUNTER] {broker.name} → MO-{open_order.pk:05d}'
                        )

                    if not dry_run:
                        imap.store(msg_id, '+FLAGS', '\\Seen')
                    continue


            # ── Handle replies to our own quotations ──────────────────────────
            if '[Quotation Reference:' in raw_body:
                qt_match = re.search(r'\[Quotation Reference: (QT-[\d]+-?v?[\d]*)\]', raw_body)
                linked = False
                if qt_match and not dry_run:
                    qt_num = qt_match.group(1)
                    try:
                        qt = Quotation.objects.select_related('lead').get(quotation_number=qt_num)
                        lead = qt.lead
                        stripped = _strip_reply_chain(raw_body)
                        stamp = timezone.now().strftime('%d %b %Y %H:%M')
                        block = (
                            f'\n\n--- Reply from {sender_name} <{sender_email}> on {stamp} ---\n'
                            f'{stripped.strip()}'
                        )
                        lead.notes = (lead.notes or '') + block
                        lead.save(update_fields=['notes'])
                        linked = True
                        self.stdout.write(self.style.SUCCESS(
                            f'  [REPLY-LINKED] {sender_email} → {qt_num} (Lead #{lead.pk})'
                        ))
                    except Exception as exc:
                        self.stdout.write(f'  [REPLY-ERR]    {exc}')
                if not linked:
                    self.stdout.write(f'  [SKIP-REPLY]   From: {sender_email} | Subject: {subject[:60]}')
                if not dry_run:
                    imap.store(msg_id, '+FLAGS', '\\Seen')
                continue

            text = f"Subject: {subject}\n\n{body}"

            # ── LLM classification ────────────────────────────────────────────
            is_inquiry = classify_message(text)

            if not is_inquiry:
                self.stdout.write(f'  [NOT-INQUIRY]  From: {sender_email} | Subject: {subject[:60]}')
                if not dry_run:
                    imap.store(msg_id, '+FLAGS', '\\Seen')
                continue

            # ── Create Lead ───────────────────────────────────────────────────
            self.stdout.write(
                self.style.SUCCESS(f'  [INQUIRY]      From: {sender_email} | Subject: {subject[:60]}')
            )
            if not dry_run:
                broker = _find_broker(sender_email)
                lead = Lead.objects.create(
                    source='email',
                    raw_text=text,
                    customer_name=sender_name,
                    customer_email=sender_email,
                    status='new',
                    broker=broker
                )
                if broker:
                    MarketOrder.objects.create(
                        broker=broker,
                        lead=lead,
                        product_details=body,
                        sub_team='primary',
                        status='new',
                        created_by=None
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'   [MARKET-ORDER] Created for broker {broker.name}'
                    ))
                imap.store(msg_id, '+FLAGS', '\\Seen')
        imap.logout()

        if not dry_run:
            config.last_polled_at = timezone.now()
            config.save(update_fields=['last_polled_at'])

