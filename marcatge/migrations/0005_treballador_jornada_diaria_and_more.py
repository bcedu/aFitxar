# Generated by Django 5.1.6 on 2025-02-09 09:35

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcatge', '0004_alter_marcatge_dia_treball'),
    ]

    operations = [
        migrations.AddField(
            model_name='treballador',
            name='jornada_diaria',
            field=models.IntegerField(default=8, help_text='Hores de la jornada laboral de 1 dia', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(24)]),
        ),
        migrations.AlterField(
            model_name='marcatge',
            name='dia_treball',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='marcatge.diatreball'),
        ),
    ]
