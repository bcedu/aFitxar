# Generated by Django 5.1.6 on 2025-02-09 10:23

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcatge', '0006_diatreball_hores_restants'),
    ]

    operations = [
        migrations.AlterField(
            model_name='treballador',
            name='jornada_diaria',
            field=models.DecimalField(decimal_places=2, default=8, help_text="Hores de la jornada laboral de 1 dia. Atenció: '1.5' son '1h 30m'.", max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(24)]),
        ),
    ]
