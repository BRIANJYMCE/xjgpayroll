from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from user_account.models import TimeLog
from admin_account.models import WorkAssignment, WorkType

User = get_user_model()

class TimeLogMidnightTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create(username="testuser")

        # Create a dummy work type and task
        self.work_type = WorkType.objects.create(name="Development", is_active=True)
        self.task = WorkAssignment.objects.create(user=self.user)  # ✅ removed "status"
        self.task.work_types.add(self.work_type)

    def test_shift_across_midnight(self):
        """
        Simulate a shift from 11:00 PM to 1:00 AM (next day).
        It should compute 2.0 hours, not a negative value.
        """
        # Start at 11:00 PM yesterday
        time_in = timezone.now().replace(hour=23, minute=0, second=0, microsecond=0)
        # End at 1:00 AM today
        time_out = time_in + timedelta(hours=2)

        log = TimeLog.objects.create(
            user=self.user,
            task=self.task,
            time_in=time_in,
            time_out=time_out,
        )

        # Calculate total hours
        delta = log.time_out - log.time_in
        total_hours = round(delta.total_seconds() / 3600, 2)

        # Print for debugging
        print(f"\n[DEBUG] Time In: {log.time_in}, Time Out: {log.time_out}, Hours: {total_hours}")

        self.assertEqual(total_hours, 2.0, f"Expected 2.0 hours, got {total_hours}")
