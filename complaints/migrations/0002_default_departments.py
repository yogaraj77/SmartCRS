from django.db import migrations


def create_default_departments(apps, schema_editor):
    Department = apps.get_model("complaints", "Department")
    departments = [
        "Hostel Department",
        "Transport Department",
        "IT Department",
        "Library Staff",
        "Maintenance Team",
    ]

    for name in departments:
        Department.objects.get_or_create(name=name)


def remove_default_departments(apps, schema_editor):
    Department = apps.get_model("complaints", "Department")
    Department.objects.filter(
        name__in=[
            "Hostel Department",
            "Transport Department",
            "IT Department",
            "Library Staff",
            "Maintenance Team",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_departments, remove_default_departments),
    ]
