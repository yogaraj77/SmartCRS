from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("index.html", views.landing, name="landing_html"),
    path("departments/", views.departments_page, name="departments"),
    path("departments.html", views.departments_page, name="departments_html"),
    path("support/", views.support_page, name="support"),
    path("support.html", views.support_page, name="support_html"),
    path("login/", views.login_view, name="login"),
    path("login.html", views.login_view, name="login_html"),
    path("register/", views.register_student, name="register"),
    path("register.html", views.register_student, name="register_html"),
    path("faculty/register/", views.register_faculty, name="faculty_register"),
    path("faculty-register.html", views.register_faculty, name="faculty_register_html"),
    path("admin-signup/", views.register_admin, name="admin_register"),
    path("admin-register.html", views.register_admin, name="admin_register_html"),
    path("logout/", views.logout_view, name="logout"),
    path("redirect/", views.role_redirect, name="role_redirect"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/complaints/new/", views.raise_complaint, name="raise_complaint"),
    path("student/complaints/", views.my_complaints, name="my_complaints"),
    path("student/history/", views.complaint_history, name="complaint_history"),
    path("complaints/<str:complaint_id>/", views.complaint_detail, name="complaint_detail"),
    path("staff/dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
]
