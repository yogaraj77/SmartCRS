from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from .models import Complaint, Department


class LoginForm(forms.Form):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("staff", "Staff"),
        ("admin", "Admin"),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES)
    user_id = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class StudentRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    student_id = forms.CharField(max_length=30)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_student_id(self):
        student_id = self.cleaned_data["student_id"].strip()
        if User.objects.filter(username=student_id).exists():
            raise forms.ValidationError("This student ID is already registered.")
        return student_id

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["title", "category", "priority", "description", "attachment"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "maxlength": 500}),
        }


class StaffComplaintUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            (Complaint.ASSIGNED, "Assigned"),
            (Complaint.IN_PROGRESS, "In Progress"),
            (Complaint.RESOLVED, "Resolved"),
        ]
    )
    remark = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ["name", "description"]


class StaffCreateForm(forms.Form):
    staff_id = forms.CharField(max_length=30)
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    department = forms.ModelChoiceField(queryset=Department.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.all()

    def clean_staff_id(self):
        staff_id = self.cleaned_data["staff_id"].strip()
        if User.objects.filter(username=staff_id).exists():
            raise forms.ValidationError("This staff ID is already registered.")
        return staff_id


class FacultyRegistrationForm(forms.Form):
    staff_id = forms.CharField(max_length=30)
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    department = forms.ModelChoiceField(queryset=Department.objects.none())
    passkey = forms.CharField(widget=forms.PasswordInput)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["department"].queryset = Department.objects.all()

    def clean_staff_id(self):
        staff_id = self.cleaned_data["staff_id"].strip()
        if User.objects.filter(username=staff_id).exists():
            raise forms.ValidationError("This faculty ID is already registered.")
        return staff_id

    def clean_passkey(self):
        passkey = self.cleaned_data["passkey"]
        if passkey != settings.STAFF_REGISTRATION_KEY:
            raise forms.ValidationError("Invalid staff registration passkey.")
        return passkey

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class AdminRegistrationForm(forms.Form):
    admin_id = forms.CharField(max_length=30)
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    admin_key = forms.CharField(widget=forms.PasswordInput)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    def clean_admin_id(self):
        admin_id = self.cleaned_data["admin_id"].strip()
        if User.objects.filter(username=admin_id).exists():
            raise forms.ValidationError("This admin ID is already registered.")
        return admin_id

    def clean_admin_key(self):
        admin_key = self.cleaned_data["admin_key"]
        if admin_key != settings.ADMIN_REGISTRATION_KEY:
            raise forms.ValidationError("Invalid admin registration key.")
        return admin_key

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
