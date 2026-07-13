# Generated for Smart Complaint Routing System model alignment.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0002_default_departments"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="complaint",
            name="category",
            field=models.CharField(
                choices=[
                    ("Hostel", "Hostel"),
                    ("Transport", "Transport"),
                    ("IT Support", "IT Support"),
                    ("Library", "Library"),
                    ("Maintenance", "Maintenance"),
                    ("Classroom", "Classroom"),
                ],
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="ComplaintStatus",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Pending", "Pending"),
                            ("Assigned", "Assigned"),
                            ("In Progress", "In Progress"),
                            ("Resolved", "Resolved"),
                        ],
                        max_length=20,
                    ),
                ),
                ("remark", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "complaint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_history",
                        to="complaints.complaint",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="complaint_status_updates",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "Complaint statuses",
                "ordering": ["-created_at"],
            },
        ),
    ]
