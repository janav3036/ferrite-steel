"""
Management command: python manage.py poll_emails

Connects to each active TeamEmailConfig inbox via IMAP, fetches UNSEEN messages,
classifies them, and creates Leads for genuine product inquiries.
"""
import email
import imaplib
import io
import re
from email.header import decode_header
from datetime import timedelta

from django.core.management.base import BaseCommand

from django.utils import timezone

from quotations.models import Lead, Quotation, TeamEmailConfig, MarketOrder
from database.models import Broker
from quotations.services.llm import classify_message, classify_broker_response
from training.services.extractor import extract_text
from aegis.models import CustomUser
from aegis.notifications import notify

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

def _extract_attachments_text(msg):
    """Extract text from PDF/DOCX/Excel attachments and return it as a labelled block."""
    if not msg.is_multipart():
        return ''
    parts = []
    for part in msg.walk():
        filename = part.get_filename()
        if not filename:
            continue
        filename = ''.join(_decode(f, enc) for f, enc in decode_header(filename))
        if not filename.lower().endswith(('.pdf', '.docx', '.xlsx', 'xls')):
            continue

        payload = part.get_payload(decode=True)
        if not payload:
            continue

        try:
            text = extract_text(io.BytesIO(payload), filename)
        except Exception:
            continue

        if text.strip():
            parts.append(f'--- Attachment: {filename} ----\n{text.strip()}')

    return '\n\n'.join(parts)

def _parse_sender(from_header):
    """Return (name, email) from a From header string."""
    name, addr = email.utils.parseaddr(from_header or '')
    parts = decode_header(name)
    name = ''.join(_decode(part, enc) for part, enc in parts).strip()
    return name, addr.lower()

def _get_recipients(team_slug):
    """Return active users of the given team plus all admins (distinct)."""
    team_users = CustomUser.objects.filter(team=team_slug, is_active=True)
    admins = CustomUser.objects.filter(role='admin', is_active=True)
    return (team_users | admins).distinct()

def _find_broker(email_addr: str):
    """Return the active Broker whose email matches sender, or None."""
    if not email_addr:
        return None
    return Broker.objects.filter(email__iexact=email_addr, is_active=True).first()


_MSGID_RE = re.compile(r'<[^<>\s]+>')


def _extract_referenced_ids(msg):
    """Return the set of Message-IDs this message's In-Reply-To/References headers point to."""
    raw = ' '.join(filter(None, [msg.get('In-Reply-To', ''), msg.get('References', '')]))
    return set(_MSGID_RE.findall(raw))


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

        try:
            _, data = imap.search(None, 'UNSEEN')
            msg_ids = data[0].split()

            if not msg_ids:
                self.stdout.write('  No new messages.')
                if not dry_run:
                    config.last_polled_at = timezone.now()
                    config.save(update_fields=['last_polled_at'])
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
                attachment_text = _extract_attachments_text(msg)
                if attachment_text:
                    body = f'{body}\n\n{attachment_text}'.strip()

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

                                recipients = _get_recipients('market')
                                notify(
                                    recipients,
                                    f'Broker confirmed: {broker.name}',
                                    message=f'MO-{open_order.pk:05d} status → broker confirmed.',
                                    link=f'/quotations/market-orders/{open_order.pk}/',
                                    notif_type='general',
                                )
                                
                            elif response_type == 'counter':
                                recipients = _get_recipients('market')
                                notify(
                                    recipients,
                                    f'Broker counter-reply: {broker.name}',
                                    message=f'MO-{open_order.pk:05d} — broker sent a counter offer.',
                                    link=f'/quotations/market-orders/{open_order.pk}/',
                                    notif_type='general',
                                )


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

                    # Broker email but no open rate_sent order — treat as a new inquiry
                    self.stdout.write(self.style.SUCCESS(
                        f'  [BROKER-NEW]   {broker.name} — new inquiry, creating lead + market order'
                    ))
                    if not dry_run:
                        new_lead = Lead.objects.create(
                            source='email',
                            raw_text=f"Subject: {subject}\n\n{body}",
                            customer_name=broker.name,
                            customer_email=sender_email,
                            status='new',
                            broker=broker,
                            received_via=config,
                        )
                        MarketOrder.objects.create(
                            broker=broker,
                            lead=new_lead,
                            product_details=body,
                            sub_team='primary',
                            status='new',
                            created_by=None,
                        )
                        recipients = _get_recipients(config.team)
                        notify(
                            recipients,
                            f'New broker inquiry: {broker.name}',
                            message=f'Subject: {subject[:80]}',
                            link=f'/quotations/leads/{new_lead.pk}/',
                            notif_type='lead_created',
                        )
                        imap.store(msg_id, '+FLAGS', '\\Seen')
                    continue

                # ── Handle replies to our own quotations ──────────────────────────
                # Primary signal: In-Reply-To/References headers matched against the
                # Message-ID we stamped on the outbound quotation email (reliable —
                # not user-editable, survives client-side quoting differences).
                referenced_ids = _extract_referenced_ids(msg)
                replied_quotation = None
                if referenced_ids:
                    replied_quotation = Quotation.objects.select_related('lead').filter(
                        sent_message_id__in=referenced_ids
                    ).first()

                # Fallback: legacy text marker, for quotations sent before this field
                # existed or if a client strips headers.
                has_marker = '[Quotation Reference:' in raw_body
                if replied_quotation is None and has_marker:
                    qt_match = re.search(r'\[Quotation Reference: (QT-[\d]+-?v?[\d]*)\]', raw_body)
                    if qt_match:
                        replied_quotation = Quotation.objects.select_related('lead').filter(
                            quotation_number=qt_match.group(1)
                        ).first()

                if replied_quotation is not None or has_marker:
                    linked = False
                    if replied_quotation is not None and not dry_run:
                        lead = replied_quotation.lead
                        stripped = body
                        stamp = timezone.now().strftime('%d %b %Y %H:%M')
                        block = (
                            f'\n\n--- Reply from {sender_name} <{sender_email}> on {stamp} ---\n'
                            f'{stripped.strip()}'
                        )
                        lead.notes = (lead.notes or '') + block
                        lead.save(update_fields=['notes'])
                        linked = True
                        recipients = _get_recipients(config.team)
                        notify(
                            recipients,
                            f'Reply received: {replied_quotation.quotation_number}',
                            message=f'{sender_name or sender_email} replied - Lead #{lead.pk}',
                            link=f'/quotations/leads/{lead.pk}/',
                            notif_type='general',
                        )
                        self.stdout.write(self.style.SUCCESS(
                            f'  [REPLY-LINKED] {sender_email} → {replied_quotation.quotation_number} (Lead #{lead.pk})'
                        ))
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
                    lead = Lead.objects.create(
                        source='email',
                        raw_text=text,
                        customer_name=sender_name,
                        customer_email=sender_email,
                        status='new',
                        received_via=config,
                    )
                    recipients = _get_recipients(config.team)
                    notify(
                        recipients,
                        f'New lead from email: {sender_name or sender_email}',
                        message=f'Subject: {subject[:80]}',
                        link=f'/quotations/leads/{lead.pk}/',
                        notif_type='lead_created'
                    )
                    imap.store(msg_id, '+FLAGS', '\\Seen')

            if not dry_run:
                config.last_polled_at = timezone.now()
                config.save(update_fields=['last_polled_at'])
        finally:
            imap.logout()

