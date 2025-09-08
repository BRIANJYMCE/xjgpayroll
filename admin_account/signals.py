from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WorkType
from user_account.models import TimeLog

@receiver(post_save, sender=WorkType)
def cleanup_ongoing_logs_on_archive(sender, instance, **kwargs):
    """
    Delete ongoing timelogs (no time_out) when a WorkType is archived.
    Completed logs stay untouched.
    """
    if not instance.is_active:  # Archived
        TimeLog.objects.filter(
            task__work_types=instance,
            time_out__isnull=True
        ).delete()
