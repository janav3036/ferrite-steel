from .models import Notification


def notify(users, title, message='', link='', notif_type='general'):
    """
    Create notifications for one or more users.
    `users` can be a queryset or list of CustomUser instances.
    """
    to_create = [
        Notification(user=u, title=title, message=message, link=link, type=notif_type)
        for u in users
    ]
    if to_create:
        Notification.objects.bulk_create(to_create)
