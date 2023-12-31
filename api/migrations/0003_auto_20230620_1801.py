# Generated by Django 3.2.7 on 2023-06-20 21:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0002_profile_turn_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='pacient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='reservation',
            name='turn',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.turn'),
        ),
        migrations.AlterField(
            model_name='turn',
            name='therapist',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
