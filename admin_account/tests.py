from django.test import TestCase, LiveServerTestCase
from django.urls import reverse
from django.utils.timezone import make_aware, now
from datetime import timedelta, datetime
from django.contrib.auth.models import User
from admin_account.models import WorkType, WorkAssignment
from user_account.models import TimeLog


class WeeklyPayrollTest(TestCase):
    def setUp(self):
        # Create superuser for testing admin views
        self.admin = User.objects.create_superuser(
            username="admin_tester",
            password="admin123",
            email="admin@example.com"
        )
        self.client.login(username="admin_tester", password="admin123")

        # Create normal test user
        self.user = User.objects.create_user(username="payroll_tester", password="test123")

        # Create dummy work type
        self.work_type = WorkType.objects.create(name="Testing Task")

        # Create a WorkAssignment for this user and link work_type
        self.assignment = WorkAssignment.objects.create(user=self.user)
        self.assignment.work_types.add(self.work_type)

        # Insert 5 weeks of logs
        base_date = now().date()
        for i in range(5):
            day = base_date - timedelta(days=i * 7)
            time_in = make_aware(datetime.combine(day, datetime.min.time())) + timedelta(hours=9)
            time_out = time_in + timedelta(hours=4)

            TimeLog.objects.create(
                user=self.user,
                task=self.assignment,
                work_type=self.work_type,
                time_in=time_in,
                time_out=time_out,
            )

    def test_week_list_view(self):
        url = reverse("user_week_list", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Weekly Payroll")  # sanity check

    def test_week_summary_view(self):
        week_start = (now().date() - timedelta(days=28))  # 4 weeks ago Monday
        url = reverse("user_weekly_summary", args=[self.user.id, week_start.strftime("%Y-%m-%d")])

        # POST with a rate to trigger total_pay
        response = self.client.post(url, {"rate": "100"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Pay")
        self.assertContains(response, "₱400")  # 4 hrs * 100 rate


# 👇 Add this class for manual browser testing
class WeeklyPayrollLiveTest(LiveServerTestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin_tester", password="admin123", email="admin@example.com"
        )
        self.user = User.objects.create_user(username="payroll_tester", password="test123")

        work_type = WorkType.objects.create(name="Testing Task")
        assignment = WorkAssignment.objects.create(user=self.user)
        assignment.work_types.add(work_type)

        base_date = now().date()
        for i in range(5):
            day = base_date - timedelta(days=i * 7)
            time_in = make_aware(datetime.combine(day, datetime.min.time())) + timedelta(hours=9)
            time_out = time_in + timedelta(hours=4)
            TimeLog.objects.create(user=self.user, task=assignment, work_type=work_type,
                                   time_in=time_in, time_out=time_out)

    def test_open_browser(self):
        print(f"\n🚀 Test data ready!")
        print(f"Open this in your browser: {self.live_server_url}/admin_account/user-week-list/{self.user.id}/")
        input("Press Enter after checking the page...")
