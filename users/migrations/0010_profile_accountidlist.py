# Generated by Django 3.0.1 on 2020-01-16 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_auto_20200116_2224'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='accountIDList',
            field=models.CharField(blank=True, max_length=128),
        ),
    ]
