# Generated by Django 5.0.6 on 2024-06-26 14:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("backend", "0003_remove_contact_type_remove_user_family_name_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="contact",
            name="name",
        ),
    ]
