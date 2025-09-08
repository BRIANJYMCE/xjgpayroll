# admin_account/models.py
from django.db import models
from django.contrib.auth.models import User

class WorkType(models.Model):
    name = models.CharField(max_length=50, unique=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class WorkAssignment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignments")
    work_types = models.ManyToManyField(WorkType, related_name="assignments")  # <-- multiple work types
    logs_is_active_in_user = models.BooleanField(default=True)
    date_assigned = models.DateField(auto_now_add=True)

    def __str__(self):
        worktypes_str = " / ".join([wt.name for wt in self.work_types.all()])
        return f"{self.user.username} - {worktypes_str} - {self.date_assigned}"

    @property
    def status(self):
        logs = self.timelogs.all().order_by('id')
        if not logs.exists():
            return "Standby"
        elif logs.last().time_out:
            return "Finished"
        else:
            return "Ongoing"
        
class WeeklyPayroll(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="weekly_payrolls")
    week_start = models.DateField()  # Monday (or start of the week)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        unique_together = ("user", "week_start")  # prevent duplicate payrolls

    def __str__(self):
        return f"{self.user.username} | {self.week_start} | ₱{self.total_pay}"
