# Generated by Django 5.2.4 on 2025-07-20 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcatge', '0010_diatreball_marcatges_relacionats_txt_backup'),
    ]

    operations = [
        migrations.AddField(
            model_name='diatreball',
            name='forcar_jornada_diaria',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AddField(
            model_name='diatreball',
            name='nova_jornada_diaria',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
