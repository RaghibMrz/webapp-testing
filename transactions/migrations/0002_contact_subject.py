# Generated by Django 3.0.1 on 2020-01-09 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='subject',
            field=models.CharField(default='subject', max_length=64),
            preserve_default=False,
        ),
    ]