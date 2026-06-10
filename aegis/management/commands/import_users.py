from django.core.management.base import BaseCommand
from aegis.models import CustomUser

USERS = [
    # (username, first_name, last_name, phone, phone_2, team, password, email)
    ('shail88', 'Shaileshkumar', 'Doshi',    '8828335169', '9920777336', 'cs',        'shados88',  ''),
    ('rishi91', 'Rishikesh',     'Patel',    '9167622284', '',           'cs',        'rispat91',  ''),
    ('shala91', 'Shalaka',       'More',     '9167670466', '',           'cs',        'shamor91',  ''),
    ('hriti84', 'Hritik',        'Shelke',   '8422843308', '',           'cs',        'hrishe84',  'fcc@ferrite.in'),
    ('saya98',  'Sayali',        'Nagvekar', '9820732277', '',           'cs',        'sanag98',   ''),
    ('bijal84', 'Bijal',         'Mehta',    '8422843314', '',           'cs',        'bijmeh84',  ''),
    ('vaibh91', 'Vaibhavi',      'Dumal',    '9167622202', '',           'cs',        'vaidum91',  ''),
    ('shrid93', 'Shridhar',      'Shah',     '9324863535', '9819556569', 'team_9',    'shrsha93',  'gm@ferrite.in'),
    ('dhans88', 'Dhanshree',     'Mokashi',  '8828335166', '',           'team_9',    'dhamok88',  ''),
    ('atish74', 'Atish',         'Pardhi',   '7400096932', '',           'team_9',    'atipar74',  ''),
    ('ruchi91', 'Ruchita',       'Jadhav',   '9167622201', '',           'team_9',    'rucjad91',  'enquiry@ferrite.in'),
    ('santo84', 'Santosh',       'Zore',     '8433617494', '',           'team_9',    'sanzor84',  ''),
    # ruchi91 conflict: Ruchi Mohite (Corporate) skipped — confirm her username first
    ('aman84',  'Aman',          'Sharma',   '8422843309', '',           'corporate', 'amasha84',  ''),
    ('rupes99', 'Rupesh',        'Mhatre',   '9920777332', '',           'market',    'rupmha99',  ''),
    ('aakas88', 'Aakash',        'Palande',  '8828335170', '',           'market',    'aakpal88',  'iron@ferrite.in'),
    ('rajna91', 'Rajnandini',    'Gavhane',  '9167622203', '',           'market',    'rajgav91',  ''),
]


class Command(BaseCommand):
    help = 'Import initial staff users from the client-provided list'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for username, first, last, phone, phone_2, team, password, email in USERS:
            if CustomUser.objects.filter(username=username).exists():
                self.stdout.write(f'  SKIP  {username} — already exists')
                skipped += 1
                continue

            user = CustomUser(
                username=username,
                first_name=first,
                last_name=last,
                phone=phone,
                phone_2=phone_2 or None,
                team=team,
                email=email,
                role='member',
                is_active=True,
            )
            user.set_password(password)
            user.save()
            created += 1
            self.stdout.write(f'  OK    {username} — {first} {last} ({team})')

        self.stdout.write(self.style.SUCCESS(
            f'\nDone: {created} created, {skipped} skipped.'
        ))
        self.stdout.write(self.style.WARNING(
            'NOTE: Ruchi Mohite (Corporate, rucmoh91) was not imported — username conflict with ruchi91. Confirm her username and add manually.'
        ))
