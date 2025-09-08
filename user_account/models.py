from django.db import models
from django.contrib.auth.models import User
from admin_account.models import WorkAssignment, WorkType


class TimeLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(
        WorkAssignment,
        on_delete=models.SET_NULL,
        related_name="timelogs",
        null=True, blank=True
    )
    work_type = models.ForeignKey(
        WorkType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="timelogs"
    )  # <-- new field

    time_in = models.DateTimeField(null=True, blank=True)   # full datetime (date + time)
    time_out = models.DateTimeField(null=True, blank=True)  # full datetime (date + time)
    notes = models.TextField(blank=True, null=True)

    # ✅ New field to store work types at the time of creation
    work_type_names = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # If log is new or work_type_names is empty, store current work types
        if self.task and (not self.work_type_names):
            self.work_type_names = " / ".join([wt.name for wt in self.task.work_types.all()])
        super().save(*args, **kwargs)

    @property
    def completed_date(self):
        """Return the date when the shift ended (from time_out)."""
        if self.time_out:
            return self.time_out.date()
        return None

    @property
    def total_hours(self):
        """Return total hours worked in this log."""
        if self.time_in and self.time_out:
            delta = self.time_out - self.time_in
            return round(delta.total_seconds() / 3600, 2)
        return 0

    def __str__(self):
        status = "Ongoing" if not self.time_out else self.time_out.strftime("%Y-%m-%d %H:%M")
        return f"{self.user.username} | {self.time_in.strftime('%Y-%m-%d %H:%M')} - {status}"
