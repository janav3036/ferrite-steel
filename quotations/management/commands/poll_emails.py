"""
Management command: python manage.py poll_emails

Connects to each active TeamEmailConfig inbox via IMAP, fetches UNSEEN messages,
classifies them, and creates Leads for genuine product inquiries.
"""
import email
import imaplib
import re
from email.header import decode_header

from django.core.management.base import BaseCommand

from quotations.models import Lead, TeamEmailConfig
from quotations.services.llm import classify_message

# Senders we never want to create leads from
SPAM_PATTERNS = re.compile(
    r'no.?reply|noreply|newsletter|unsubscribe|donotreply|mailer-daemon|postmaster',
    re.IGNORECASE,
)


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


class Command(BaseCommand):
    help = 'Poll active team email inboxes and create Leads for product inquiries.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Classify and print results without creating Leads or marking emails as seen.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        configs = TeamEmailConfig.objects.filter(is_active=True)

        if not configs.exists():
            self.stdout.write(self.style.WARNING('No active TeamEmailConfig found. Nothing to do.'))
            return

        for config in configs:
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
            body = _parse_plain_body(msg).strip()

            # ── Pre-filter: skip automated senders ───────────────────────────
            if SPAM_PATTERNS.search(sender_email):
                self.stdout.write(f'  [SKIP-SPAM]    {sender_email}')
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
                Lead.objects.create(
                    source='email',
                    raw_text=f"Subject: {subject}\n\n{body}",
                    customer_name=sender_name,
                    customer_email=sender_email,
                    status='new',
                )
                imap.store(msg_id, '+FLAGS', '\\Seen')

        imap.logout()
