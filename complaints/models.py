from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_id = models.CharField(max_length=30, unique=True)
    role = models.CharField(max_length=20, default="Student")

    def __str__(self):
        return self.student_id


class Staff(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="staff_profile",
    )
    staff_id = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_members",
    )
    role = models.CharField(max_length=20, default="Staff")

    def __str__(self):
        department = self.department.name if self.department else "No Department"
        return f"{self.staff_id} - {department}"


class Complaint(models.Model):
    HOSTEL = "Hostel"
    TRANSPORT = "Transport"
    IT_SUPPORT = "IT Support"
    LIBRARY = "Library"
    MAINTENANCE = "Maintenance"
    CLASSROOM = "Classroom"

    CATEGORY_CHOICES = [
        (HOSTEL, "Hostel"),
        (TRANSPORT, "Transport"),
        (IT_SUPPORT, "IT Support"),
        (LIBRARY, "Library"),
        (MAINTENANCE, "Maintenance"),
        (CLASSROOM, "Classroom"),
    ]

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

    PRIORITY_CHOICES = [
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
    ]

    PENDING = "Pending"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ASSIGNED, "Assigned"),
        (IN_PROGRESS, "In Progress"),
        (RESOLVED, "Resolved"),
    ]

    complaint_id = models.CharField(max_length=20, unique=True, blank=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="complaints",
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    assigned_to = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_complaints",
    )
    attachment = models.FileField(upload_to="complaints/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if self.status == self.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        if self.status != self.RESOLVED:
            self.resolved_at = None

        super().save(*args, **kwargs)

        if not self.complaint_id:
            self.complaint_id = f"CMP{self.pk:04d}"
            super().save(update_fields=["complaint_id"])

    @property
    def progress_percent(self):
        progress = {
            self.PENDING: 25,
            self.ASSIGNED: 50,
            self.IN_PROGRESS: 75,
            self.RESOLVED: 100,
        }
        return progress.get(self.status, 25)

    @property
    def department_name(self):
        if self.assigned_to and self.assigned_to.department:
            return self.assigned_to.department.name
        return category_department_name(self.category)

    def __str__(self):
        return f"{self.complaint_id or 'New'} - {self.title}"


class ComplaintRemark(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="remarks",
    )
    staff = models.ForeignKey(
        Staff,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="remarks",
    )
    remark = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Remark for {self.complaint.complaint_id}"


class ComplaintStatus(models.Model):
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    status = models.CharField(max_length=20, choices=Complaint.STATUS_CHOICES)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="complaint_status_updates",
    )
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Complaint statuses"

    def __str__(self):
        return f"{self.complaint.complaint_id} - {self.status}"


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.CharField(max_length=255)
    complaint = models.ForeignKey(
        Complaint,
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message


CATEGORY_DEPARTMENT_MAP = {
    Complaint.HOSTEL: "Hostel Department",
    Complaint.TRANSPORT: "Transport Department",
    Complaint.IT_SUPPORT: "IT Department",
    Complaint.LIBRARY: "Library Staff",
    Complaint.MAINTENANCE: "Maintenance Team",
    Complaint.CLASSROOM: "Maintenance Team",
}


def category_department_name(category):
    return CATEGORY_DEPARTMENT_MAP.get(category, "General Department")


def default_department_names():
    return list(CATEGORY_DEPARTMENT_MAP.values())
