from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AdminRegistrationForm,
    ComplaintForm,
    DepartmentForm,
    FacultyRegistrationForm,
    LoginForm,
    StaffCreateForm,
    StaffComplaintUpdateForm,
    StudentRegistrationForm,
)
from .models import (
    Complaint,
    ComplaintRemark,
    ComplaintStatus,
    Department,
    Notification,
    Staff,
    Student,
    category_department_name,
    default_department_names,
)


def ensure_default_departments():
    for name in default_department_names():
        Department.objects.get_or_create(name=name)


def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def user_role(user):
    if is_admin_user(user):
        return "admin"
    if hasattr(user, "staff_profile"):
        return "staff"
    if hasattr(user, "student_profile"):
        return "student"
    return "unknown"


def public_department_cards():
    ensure_default_departments()
    descriptions = {
        "Hostel Department": "Hostel rooms, water, cleanliness, power, and resident facilities.",
        "IT Department": "WiFi, computer labs, systems, account access, and network support.",
        "Transport Department": "Bus routes, timing, vehicles, stops, and transport service issues.",
        "Library Staff": "Books, reading areas, library systems, and study-space support.",
        "Maintenance Team": "Classrooms, electrical faults, plumbing, repairs, and infrastructure.",
        "General Department": "Issues that need review before final department assignment.",
    }
    cards = []
    for department in Department.objects.prefetch_related("staff_members"):
        categories = [
            category
            for category, _label in Complaint.CATEGORY_CHOICES
            if category_department_name(category) == department.name
        ]
        complaint_count = Complaint.objects.filter(
            Q(assigned_to__department=department)
            | Q(assigned_to__isnull=True, category__in=categories)
        ).distinct().count()
        cards.append(
            {
                "name": department.name,
                "description": department.description or descriptions.get(
                    department.name,
                    "Handles routed college facility complaints.",
                ),
                "staff_count": department.staff_members.count(),
                "complaint_count": complaint_count,
                "categories": ", ".join(categories) if categories else "Manual review",
                "initial": department.name[:2].upper(),
            }
        )
    return cards


def public_category_rows():
    route_notes = {
        Complaint.HOSTEL: "Rooms, mess, water, cleanliness, power, and residential facilities.",
        Complaint.TRANSPORT: "Bus routes, delays, stops, vehicles, and transport availability.",
        Complaint.IT_SUPPORT: "Network, WiFi, lab systems, software, login, and device support.",
        Complaint.LIBRARY: "Books, issue desk, reading spaces, systems, and library facilities.",
        Complaint.MAINTENANCE: "Electrical, plumbing, repair, safety, and infrastructure work.",
        Complaint.CLASSROOM: "Projector, benches, lights, fans, boards, and classroom equipment.",
    }
    rows = []
    for category, label in Complaint.CATEGORY_CHOICES:
        complaints = Complaint.objects.filter(category=category)
        rows.append(
            {
                "category": label,
                "department": category_department_name(category),
                "active_count": complaints.exclude(status=Complaint.RESOLVED).count(),
                "resolved_count": complaints.filter(status=Complaint.RESOLVED).count(),
                "note": route_notes.get(category, "Routed by category to the responsible department."),
            }
        )
    return rows


def landing(request):
    ensure_default_departments()
    complaints = Complaint.objects.select_related("assigned_to", "assigned_to__department")
    context = {
        "total_count": complaints.count(),
        "progress_count": complaints.filter(status=Complaint.IN_PROGRESS).count(),
        "resolved_count": complaints.filter(status=Complaint.RESOLVED).count(),
    }
    return render(request, "index.html", context)


def departments_page(request):
    ensure_default_departments()
    department_cards = public_department_cards()
    return render(
        request,
        "departments.html",
        {
            "departments": Department.objects.prefetch_related("staff_members"),
            "department_cards": department_cards,
            "department_count": len(department_cards),
            "staff_count": Staff.objects.count(),
            "total_count": Complaint.objects.count(),
        },
    )


def support_page(request):
    return render(
        request,
        "support.html",
        {
            "category_map": {
                category: category_department_name(category)
                for category, _label in Complaint.CATEGORY_CHOICES
            },
            "category_rows": public_category_rows(),
            "total_count": Complaint.objects.count(),
            "resolved_count": Complaint.objects.filter(status=Complaint.RESOLVED).count(),
            "progress_count": Complaint.objects.filter(status=Complaint.IN_PROGRESS).count(),
        },
    )


def role_redirect(request):
    role = user_role(request.user)
    if role == "admin":
        return redirect("admin_dashboard")
    if role == "staff":
        return redirect("staff_dashboard")
    if role == "student":
        return redirect("student_dashboard")
    return redirect("login")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("role_redirect")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        role = form.cleaned_data["role"]
        user_id = form.cleaned_data["user_id"]
        password = form.cleaned_data["password"]
        user = authenticate(request, username=user_id, password=password)

        if user is None:
            messages.error(request, "Invalid ID or password.")
        elif role == "student" and not hasattr(user, "student_profile"):
            messages.error(request, "This account is not registered as a student.")
        elif role == "staff" and not hasattr(user, "staff_profile"):
            messages.error(request, "This account is not registered as staff.")
        elif role == "admin" and not is_admin_user(user):
            messages.error(request, "This account does not have admin access.")
        else:
            login(request, user)
            return redirect("role_redirect")

    return render(request, "login.html", {"form": form})


def register_student(request):
    if request.user.is_authenticated:
        return redirect("role_redirect")

    form = StudentRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        student_id = form.cleaned_data["student_id"]
        full_name = form.cleaned_data["full_name"]
        user = User.objects.create_user(
            username=student_id,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=full_name,
        )
        Student.objects.create(user=user, student_id=student_id)
        messages.success(request, "Registration successful. Please log in.")
        return redirect("login")

    return render(request, "register.html", {"form": form})


def register_faculty(request):
    if request.user.is_authenticated:
        return redirect("role_redirect")

    ensure_default_departments()
    form = FacultyRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        staff_id = form.cleaned_data["staff_id"]
        user = User.objects.create_user(
            username=staff_id,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data["full_name"],
        )
        Staff.objects.create(
            user=user,
            staff_id=staff_id,
            department=form.cleaned_data["department"],
        )
        messages.success(
            request,
            "Faculty registration successful. Please log in as Faculty.",
        )
        return redirect("login")

    return render(request, "faculty-register.html", {"form": form})


def register_admin(request):
    if request.user.is_authenticated:
        return redirect("role_redirect")

    form = AdminRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        admin_id = form.cleaned_data["admin_id"]
        User.objects.create_user(
            username=admin_id,
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data["full_name"],
            is_staff=True,
            is_superuser=True,
        )
        messages.success(
            request,
            "Admin registration successful. Please log in as Admin.",
        )
        return redirect("login")

    return render(request, "admin-register.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


def get_student_or_redirect(request):
    if not hasattr(request.user, "student_profile"):
        messages.error(request, "Student access required.")
        return None
    return request.user.student_profile


def get_staff_or_redirect(request):
    if not hasattr(request.user, "staff_profile"):
        messages.error(request, "Staff access required.")
        return None
    return request.user.staff_profile


def route_staff_for_category(category):
    ensure_default_departments()
    department_name = category_department_name(category)
    department, _ = Department.objects.get_or_create(name=department_name)
    return (
        Staff.objects.filter(department=department)
        .select_related("user", "department")
        .order_by("id")
        .first()
    )


def staff_can_access_complaint(staff, complaint):
    if complaint.assigned_to == staff:
        return True
    if (
        staff.department_id
        and complaint.assigned_to
        and complaint.assigned_to.department_id == staff.department_id
    ):
        return True
    return (
        complaint.assigned_to is None
        and staff.department
        and category_department_name(complaint.category) == staff.department.name
    )


def record_status(complaint, user, remark=""):
    ComplaintStatus.objects.create(
        complaint=complaint,
        status=complaint.status,
        updated_by=user if user.is_authenticated else None,
        remark=remark,
    )


def student_common_context(request):
    notifications = request.user.notifications.select_related("complaint")[:5]
    return {"notifications": notifications}


@login_required
def student_dashboard(request):
    student = get_student_or_redirect(request)
    if not student:
        return redirect("role_redirect")

    complaints = student.complaints.select_related("assigned_to", "assigned_to__department")
    context = {
        "student": student,
        "total_count": complaints.count(),
        "pending_count": complaints.filter(status=Complaint.PENDING).count(),
        "progress_count": complaints.filter(status=Complaint.IN_PROGRESS).count(),
        "resolved_count": complaints.filter(status=Complaint.RESOLVED).count(),
        "recent_complaints": complaints[:5],
        **student_common_context(request),
    }
    return render(request, "studentspage-dash.html", context)


@login_required
def raise_complaint(request):
    student = get_student_or_redirect(request)
    if not student:
        return redirect("role_redirect")

    form = ComplaintForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        complaint = form.save(commit=False)
        complaint.student = student
        complaint.assigned_to = route_staff_for_category(complaint.category)
        complaint.status = Complaint.ASSIGNED if complaint.assigned_to else Complaint.PENDING
        complaint.save()
        record_status(complaint, request.user, "Complaint submitted and routed.")

        if complaint.assigned_to:
            message = (
                f"{complaint.complaint_id} was routed to "
                f"{complaint.department_name}."
            )
            Notification.objects.create(
                user=complaint.assigned_to.user,
                complaint=complaint,
                message=f"New complaint assigned: {complaint.title}",
            )
        else:
            message = (
                f"{complaint.complaint_id} was received and is waiting "
                "for staff assignment."
            )

        Notification.objects.create(
            user=request.user,
            complaint=complaint,
            message=message,
        )
        messages.success(request, "Complaint submitted successfully.")
        return redirect("my_complaints")

    return render(
        request,
        "studentspage-complaints.html",
        {"form": form, "student": student, **student_common_context(request)},
    )


@login_required
def my_complaints(request):
    student = get_student_or_redirect(request)
    if not student:
        return redirect("role_redirect")

    complaints = student.complaints.select_related("assigned_to", "assigned_to__department")
    status = request.GET.get("status", "all")
    search = request.GET.get("q", "").strip()

    if status != "all":
        complaints = complaints.filter(status=status)
    if search:
        complaints = complaints.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(complaint_id__icontains=search)
            | Q(category__icontains=search)
        )

    return render(
        request,
        "studentspage-mycomplaints.html",
        {
            "student": student,
            "complaints": complaints,
            "selected_status": status,
            "search": search,
            "status_choices": Complaint.STATUS_CHOICES,
            **student_common_context(request),
        },
    )


@login_required
def complaint_history(request):
    student = get_student_or_redirect(request)
    if not student:
        return redirect("role_redirect")

    search = request.GET.get("q", "").strip()
    complaints = student.complaints.filter(status=Complaint.RESOLVED)
    if search:
        complaints = complaints.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(complaint_id__icontains=search)
            | Q(category__icontains=search)
        )

    return render(
        request,
        "studentspage-history.html",
        {
            "student": student,
            "complaints": complaints,
            "search": search,
            "resolved_count": complaints.count(),
            **student_common_context(request),
        },
    )


@login_required
def staff_dashboard(request):
    staff = get_staff_or_redirect(request)
    if not staff:
        return redirect("role_redirect")

    if request.method == "POST":
        complaint = get_object_or_404(Complaint, pk=request.POST.get("complaint_pk"))
        if not staff_can_access_complaint(staff, complaint):
            messages.error(request, "You can only update complaints assigned to your department.")
            return redirect("staff_dashboard")

        form = StaffComplaintUpdateForm(request.POST)
        if form.is_valid():
            complaint.status = form.cleaned_data["status"]
            if complaint.assigned_to is None:
                complaint.assigned_to = staff
            complaint.save()

            remark_text = form.cleaned_data.get("remark", "").strip()
            if remark_text:
                ComplaintRemark.objects.create(
                    complaint=complaint,
                    staff=staff,
                    remark=remark_text,
                )

            Notification.objects.create(
                user=complaint.student.user,
                complaint=complaint,
                message=f"{complaint.complaint_id} status updated to {complaint.status}.",
            )
            record_status(complaint, request.user, remark_text)
            messages.success(request, "Complaint updated successfully.")
        return redirect("staff_dashboard")

    department_categories = []
    if staff.department:
        for category, department_name in {
            choice[0]: category_department_name(choice[0])
            for choice in Complaint.CATEGORY_CHOICES
        }.items():
            if department_name == staff.department.name:
                department_categories.append(category)

    complaints = Complaint.objects.select_related(
        "student",
        "student__user",
        "assigned_to",
        "assigned_to__department",
    ).filter(
        Q(assigned_to=staff)
        | Q(assigned_to__department=staff.department)
        | Q(assigned_to__isnull=True, category__in=department_categories)
    ).distinct()

    status = request.GET.get("status", "all")
    search = request.GET.get("q", "").strip()
    if status != "all":
        complaints = complaints.filter(status=status)
    if search:
        complaints = complaints.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(complaint_id__icontains=search)
            | Q(student__student_id__icontains=search)
        )

    context = {
        "staff": staff,
        "complaints": complaints,
        "total_count": complaints.count(),
        "pending_count": complaints.filter(status=Complaint.PENDING).count(),
        "assigned_count": complaints.filter(status=Complaint.ASSIGNED).count(),
        "progress_count": complaints.filter(status=Complaint.IN_PROGRESS).count(),
        "resolved_count": complaints.filter(status=Complaint.RESOLVED).count(),
        "status_choices": Complaint.STATUS_CHOICES,
        "selected_status": status,
        "search": search,
    }
    return render(request, "staff-dashboard.html", context)


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    ensure_default_departments()

    department_form = DepartmentForm()
    staff_form = StaffCreateForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add_department":
            department_form = DepartmentForm(request.POST)
            if department_form.is_valid():
                department_form.save()
                messages.success(request, "Department saved successfully.")
                return redirect("admin_dashboard")

        elif action == "create_staff":
            staff_form = StaffCreateForm(request.POST)
            if staff_form.is_valid():
                staff_id = staff_form.cleaned_data["staff_id"]
                user = User.objects.create_user(
                    username=staff_id,
                    email=staff_form.cleaned_data["email"],
                    password=staff_form.cleaned_data["password"],
                    first_name=staff_form.cleaned_data["full_name"],
                )
                Staff.objects.create(
                    user=user,
                    staff_id=staff_id,
                    department=staff_form.cleaned_data["department"],
                )
                messages.success(request, "Staff account created successfully.")
                return redirect("admin_dashboard")

        elif action == "assign_staff":
            staff = get_object_or_404(Staff, pk=request.POST.get("staff_pk"))
            department = get_object_or_404(Department, pk=request.POST.get("department_pk"))
            staff.department = department
            staff.save(update_fields=["department"])
            messages.success(request, "Staff department updated.")
            return redirect("admin_dashboard")

        elif action == "assign_complaint":
            complaint = get_object_or_404(Complaint, pk=request.POST.get("complaint_pk"))
            staff = get_object_or_404(Staff, pk=request.POST.get("staff_pk"))
            complaint.assigned_to = staff
            if complaint.status == Complaint.PENDING:
                complaint.status = Complaint.ASSIGNED
            complaint.save()
            record_status(complaint, request.user, f"Assigned to {staff.staff_id}.")
            Notification.objects.create(
                user=complaint.student.user,
                complaint=complaint,
                message=f"{complaint.complaint_id} was assigned to {staff.staff_id}.",
            )
            messages.success(request, "Complaint assigned successfully.")
            return redirect("admin_dashboard")

        elif action == "delete_student":
            student = get_object_or_404(Student, pk=request.POST.get("student_pk"))
            student.user.delete()
            messages.success(request, "Student account deleted.")
            return redirect("admin_dashboard")

        elif action == "delete_staff":
            staff = get_object_or_404(Staff, pk=request.POST.get("staff_pk"))
            staff.user.delete()
            messages.success(request, "Staff account deleted.")
            return redirect("admin_dashboard")

        elif action == "delete_department":
            department = get_object_or_404(Department, pk=request.POST.get("department_pk"))
            department.delete()
            messages.success(request, "Department deleted.")
            return redirect("admin_dashboard")

    complaints = Complaint.objects.select_related(
        "student",
        "student__user",
        "assigned_to",
        "assigned_to__department",
    )
    selected_status = request.GET.get("status", "all")
    search = request.GET.get("q", "").strip()
    if selected_status != "all":
        complaints = complaints.filter(status=selected_status)
    if search:
        complaints = complaints.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
            | Q(complaint_id__icontains=search)
            | Q(category__icontains=search)
            | Q(student__student_id__icontains=search)
            | Q(assigned_to__staff_id__icontains=search)
        )

    status_counts = complaints.values("status").annotate(total=Count("id"))
    counts = {item["status"]: item["total"] for item in status_counts}

    context = {
        "department_form": department_form,
        "staff_form": staff_form,
        "departments": Department.objects.all(),
        "students": Student.objects.select_related("user"),
        "staff_members": Staff.objects.select_related("user", "department"),
        "complaints": complaints,
        "status_choices": Complaint.STATUS_CHOICES,
        "selected_status": selected_status,
        "search": search,
        "total_count": complaints.count(),
        "pending_count": counts.get(Complaint.PENDING, 0),
        "assigned_count": counts.get(Complaint.ASSIGNED, 0),
        "progress_count": counts.get(Complaint.IN_PROGRESS, 0),
        "resolved_count": counts.get(Complaint.RESOLVED, 0),
    }
    return render(request, "admin-dashboard.html", context)


@login_required
def complaint_detail(request, complaint_id):
    complaint = get_object_or_404(
        Complaint.objects.select_related(
            "student",
            "student__user",
            "assigned_to",
            "assigned_to__department",
        ).prefetch_related("remarks", "status_history"),
        complaint_id=complaint_id,
    )

    allowed = False
    if is_admin_user(request.user):
        allowed = True
    elif hasattr(request.user, "student_profile"):
        allowed = complaint.student == request.user.student_profile
    elif hasattr(request.user, "staff_profile"):
        staff = request.user.staff_profile
        allowed = staff_can_access_complaint(staff, complaint)

    if not allowed:
        messages.error(request, "You do not have access to this complaint.")
        return redirect("role_redirect")

    return render(request, "complaint-detail.html", {"complaint": complaint})
