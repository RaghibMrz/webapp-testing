# Generated by Django 3.0.1 on 2020-01-13 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_profile_userid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='userID',
            field=models.CharField(blank=True, max_length=14),
        ),
    ]
