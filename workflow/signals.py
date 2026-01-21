from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """
    Create default user groups.
    Idempotent: safe to run multiple times.
    """
    groups = {
        'Employee': [],
        'Manager': [],
        'Admin': [],
    }

    for group_name in groups.keys():
        Group.objects.get_or_create(name=group_name)
