# Generated by Django 5.1.6 on 2025-02-08 10:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formapp', '0002_alter_student_registration_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='id_photo',
            name='image',
            field=models.ImageField(upload_to='id_photos/'),
        ),
    ]
