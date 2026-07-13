from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import (
    Complaint,
    ComplaintRemark,
    ComplaintStatus,
    Department,
    Notification,
    Staff,
    Student,
)


class ComplaintSystemTests(TestCase):
    def setUp(self):
        self.hostel_department = Department.objects.get(name="Hostel Department")
        self.maintenance_department = Department.objects.get(name="Maintenance Team")
        self.it_department = Department.objects.get(name="IT Department")
        self.student_user = User.objects.create_user(
            username="S001",
            password="studentpass123",
            first_name="Student One",
        )
        self.student = Student.objects.create(
            user=self.student_user,
            student_id="S001",
        )
        self.staff_user = User.objects.create_user(
            username="STF001",
            password="staffpass123",
            first_name="Staff One",
        )
        self.staff = Staff.objects.create(
            user=self.staff_user,
            staff_id="STF001",
            department=self.hostel_department,
        )
        self.admin_user = User.objects.create_superuser(
            username="ADMIN001",
            password="adminpass123",
            email="admin@example.com",
        )

    def test_public_pages_render_with_shared_theme(self):
        for url_name in ["landing", "departments", "support", "login"]:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '<style id="internal-app-css">')

    def test_landing_page_uses_live_aggregate_complaint_data(self):
        Complaint.objects.create(
            student=self.student,
            title="Private homepage issue",
            description="This complaint should only affect public counts.",
            category=Complaint.HOSTEL,
            priority=Complaint.HIGH,
            assigned_to=self.staff,
            status=Complaint.IN_PROGRESS,
        )
        Complaint.objects.create(
            student=self.student,
            title="Resolved private homepage issue",
            description="This resolved complaint should only affect public counts.",
            category=Complaint.MAINTENANCE,
            priority=Complaint.MEDIUM,
            assigned_to=self.staff,
            status=Complaint.RESOLVED,
        )

        response = self.client.get(reverse("landing"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 2)
        self.assertEqual(response.context["progress_count"], 1)
        self.assertEqual(response.context["resolved_count"], 1)
        self.assertContains(response, "Total complaints")
        self.assertContains(response, "Complaints in progress")
        self.assertContains(response, "Complaints resolved")
        self.assertNotContains(response, "Private homepage issue")
        self.assertNotContains(response, "Resolved private homepage issue")

    def test_student_registration_creates_user_and_profile(self):
        response = self.client.post(
            reverse("register"),
            {
                "full_name": "New Student",
                "student_id": "S002",
                "email": "new@example.com",
                "password1": "strongpass123",
                "password2": "strongpass123",
            },
        )

        self.assertRedirects(response, reverse("login"))
        self.assertTrue(User.objects.filter(username="S002").exists())
        self.assertTrue(Student.objects.filter(student_id="S002").exists())

    def test_faculty_registration_creates_staff_profile_with_department(self):
        response = self.client.post(
            reverse("faculty_register"),
            {
                "staff_id": "FAC002",
                "full_name": "Faculty Two",
                "email": "faculty@example.com",
                "department": self.hostel_department.pk,
                "passkey": "STAFF123",
                "password1": "facultypass123",
                "password2": "facultypass123",
            },
        )

        self.assertRedirects(response, reverse("login"))
        staff = Staff.objects.get(staff_id="FAC002")
        self.assertEqual(staff.department, self.hostel_department)
        self.assertTrue(User.objects.filter(username="FAC002").exists())

    def test_faculty_registration_rejects_invalid_passkey(self):
        response = self.client.post(
            reverse("faculty_register"),
            {
                "staff_id": "FAC003",
                "full_name": "Faculty Three",
                "email": "faculty3@example.com",
                "department": self.hostel_department.pk,
                "passkey": "WRONG",
                "password1": "facultypass123",
                "password2": "facultypass123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="FAC003").exists())
        self.assertFalse(Staff.objects.filter(staff_id="FAC003").exists())

    def test_admin_registration_creates_admin_user(self):
        response = self.client.post(
            reverse("admin_register"),
            {
                "admin_id": "ADMIN002",
                "full_name": "Admin Two",
                "email": "admin@example.com",
                "admin_key": "ADMIN123",
                "password1": "adminpass123",
                "password2": "adminpass123",
            },
        )

        self.assertRedirects(response, reverse("login"))
        admin = User.objects.get(username="ADMIN002")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_hostel_complaint_routes_to_hostel_staff(self):
        self.client.login(username="S001", password="studentpass123")
        response = self.client.post(
            reverse("raise_complaint"),
            {
                "title": "Hostel water leakage",
                "category": Complaint.HOSTEL,
                "priority": Complaint.HIGH,
                "description": "Water leakage near room corridor.",
            },
        )

        self.assertRedirects(response, reverse("my_complaints"))
        complaint = Complaint.objects.get(title="Hostel water leakage")
        self.assertEqual(complaint.assigned_to, self.staff)
        self.assertEqual(complaint.status, Complaint.ASSIGNED)
        self.assertEqual(complaint.priority, Complaint.HIGH)
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_user,
                complaint=complaint,
            ).exists()
        )
        self.assertTrue(
            ComplaintStatus.objects.filter(
                complaint=complaint,
                status=Complaint.ASSIGNED,
            ).exists()
        )

    def test_classroom_complaint_routes_to_maintenance_staff(self):
        maintenance_user = User.objects.create_user(
            username="MNT001",
            password="maintenancepass123",
            first_name="Maintenance One",
        )
        maintenance_staff = Staff.objects.create(
            user=maintenance_user,
            staff_id="MNT001",
            department=self.maintenance_department,
        )

        self.client.login(username="S001", password="studentpass123")
        self.client.post(
            reverse("raise_complaint"),
            {
                "title": "Classroom projector issue",
                "category": Complaint.CLASSROOM,
                "priority": Complaint.MEDIUM,
                "description": "Projector is not displaying in room C-204.",
            },
        )

        complaint = Complaint.objects.get(title="Classroom projector issue")
        self.assertEqual(complaint.assigned_to, maintenance_staff)
        self.assertEqual(complaint.status, Complaint.ASSIGNED)

    def test_staff_can_update_status_and_add_remark(self):
        complaint = Complaint.objects.create(
            student=self.student,
            title="Hostel fan issue",
            description="Fan is not working.",
            category=Complaint.HOSTEL,
            priority=Complaint.MEDIUM,
            assigned_to=self.staff,
            status=Complaint.ASSIGNED,
        )

        self.client.login(username="STF001", password="staffpass123")
        response = self.client.post(
            reverse("staff_dashboard"),
            {
                "complaint_pk": complaint.pk,
                "status": Complaint.IN_PROGRESS,
                "remark": "Technician assigned.",
            },
        )

        self.assertRedirects(response, reverse("staff_dashboard"))
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.IN_PROGRESS)
        self.assertTrue(
            ComplaintRemark.objects.filter(
                complaint=complaint,
                remark="Technician assigned.",
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.student_user,
                complaint=complaint,
            ).exists()
        )

    def test_staff_cannot_update_complaints_outside_department(self):
        it_user = User.objects.create_user(
            username="IT001",
            password="itpass123",
            first_name="IT Staff",
        )
        it_staff = Staff.objects.create(
            user=it_user,
            staff_id="IT001",
            department=self.it_department,
        )
        complaint = Complaint.objects.create(
            student=self.student,
            title="Lab WiFi issue",
            description="WiFi is down in the programming lab.",
            category=Complaint.IT_SUPPORT,
            priority=Complaint.HIGH,
            assigned_to=it_staff,
            status=Complaint.ASSIGNED,
        )

        self.client.login(username="STF001", password="staffpass123")
        response = self.client.post(
            reverse("staff_dashboard"),
            {
                "complaint_pk": complaint.pk,
                "status": Complaint.RESOLVED,
                "remark": "Trying to close outside department.",
            },
        )

        self.assertRedirects(response, reverse("staff_dashboard"))
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, Complaint.ASSIGNED)

    def test_admin_dashboard_renders_and_reassigns_complaint(self):
        complaint = Complaint.objects.create(
            student=self.student,
            title="Manual assignment needed",
            description="No staff was found during initial routing.",
            category=Complaint.HOSTEL,
            priority=Complaint.LOW,
            status=Complaint.PENDING,
        )

        self.client.login(username="ADMIN001", password="adminpass123")
        get_response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "Complaint Analytics")

        response = self.client.post(
            reverse("admin_dashboard"),
            {
                "action": "assign_complaint",
                "complaint_pk": complaint.pk,
                "staff_pk": self.staff.pk,
            },
        )

        self.assertRedirects(response, reverse("admin_dashboard"))
        complaint.refresh_from_db()
        self.assertEqual(complaint.assigned_to, self.staff)
        self.assertEqual(complaint.status, Complaint.ASSIGNED)

    def test_complaint_detail_page_renders_for_owner(self):
        complaint = Complaint.objects.create(
            student=self.student,
            title="History detail check",
            description="Detail page should render timeline and metadata.",
            category=Complaint.HOSTEL,
            priority=Complaint.MEDIUM,
            assigned_to=self.staff,
            status=Complaint.IN_PROGRESS,
        )
        ComplaintStatus.objects.create(
            complaint=complaint,
            status=Complaint.IN_PROGRESS,
            updated_by=self.staff_user,
            remark="Work started.",
        )

        self.client.login(username="S001", password="studentpass123")
        response = self.client.get(reverse("complaint_detail", args=[complaint.complaint_id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "History detail check")
        self.assertContains(response, "Work started.")
