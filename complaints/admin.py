from django.contrib import admin

from .models import (
    Complaint,
    ComplaintRemark,
    ComplaintStatus,
    Department,
    Notification,
    Staff,
    Student,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "user", "role")
    search_fields = ("student_id", "user__username", "user__email")


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "user", "department", "role")
    list_filter = ("department",)
    search_fields = ("staff_id", "user__username", "user__email")


class ComplaintRemarkInline(admin.TabularInline):
    model = ComplaintRemark
    extra = 0


class ComplaintStatusInline(admin.TabularInline):
    model = ComplaintStatus
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "complaint_id",
        "title",
        "student",
        "category",
        "priority",
        "status",
        "assigned_to",
        "created_at",
    )
    list_filter = ("category", "priority", "status", "created_at")
    search_fields = ("complaint_id", "title", "student__student_id")
    inlines = [ComplaintStatusInline, ComplaintRemarkInline]


@admin.register(ComplaintRemark)
class ComplaintRemarkAdmin(admin.ModelAdmin):
    list_display = ("complaint", "staff", "created_at")
    search_fields = ("complaint__complaint_id", "remark")


@admin.register(ComplaintStatus)
class ComplaintStatusAdmin(admin.ModelAdmin):
    list_display = ("complaint", "status", "updated_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("complaint__complaint_id", "remark")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "message", "complaint", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("user__username", "message")
