from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission

from .models import CustomUser


def _perm(app_label, codename):
    try:
        return Permission.objects.get(content_type__app_label=app_label, codename=codename)
    except Permission.DoesNotExist:
        return None


BASE = lambda: [
    _perm('quotations', 'add_quotation'),
    _perm('quotations', 'change_quotation'),
    _perm('quotations', 'add_lead'),
    _perm('quotations', 'change_lead'),
    _perm('database', 'view_customer'),
    _perm('database', 'add_customer'),
    _perm('database', 'view_product'),
    _perm('training', 'view_case')
]

LEAD_EXTRA = lambda: [
    _perm('quotations', 'can_approve_quotation'),
    _perm('quotations', 'can_assign_loading_dock'),
    _perm('database', 'can_reassign_customer'),
    _perm('aegis', 'can_view_user_list'),
    _perm('training', 'add_case'),
    _perm('training', 'change_case'),
    _perm('training', 'delete_case'),

]

MARKET_EXTRA = lambda: [
    _perm('quotations', 'can_create_market_order'),
]

LOADING_DOCK_EXTRA = lambda: [
    _perm('quotations', 'can_update_do'),
]


@receiver(post_save, sender=CustomUser)
def assign_role_permissions(sender, instance, **kwargs):
    if instance.is_superuser:
        return

    role = instance.role
    team = instance.team

    if role == 'admin':
        perms = (
            BASE() + LEAD_EXTRA() + MARKET_EXTRA() + LOADING_DOCK_EXTRA()
            + [_perm('aegis', 'can_manage_users')]
        )
    elif role == 'lead':
        perms = BASE() + LEAD_EXTRA()
        if team == 'market':
            perms += MARKET_EXTRA() + LOADING_DOCK_EXTRA()
    elif role == 'loading_dock':
        perms = BASE() + LOADING_DOCK_EXTRA()
        if team == 'market':
            perms += MARKET_EXTRA()
    elif role in ('member', 'primary', 'rolling'):
        perms = BASE()
        if team == 'market':
            perms += MARKET_EXTRA()
    else:
        perms = BASE()

    instance.user_permissions.set([p for p in perms if p is not None])
