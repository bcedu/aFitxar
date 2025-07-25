# Generated by Django 5.2.4 on 2025-07-21 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcatge', '0012_alter_diatreball_forcar_jornada_diaria_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='diatreball',
            name='forcar_jornada_diaria',
            field=models.BooleanField(default=False, verbose_name='Jornada laboral diferent de la del treballador?'),
        ),
        migrations.AlterField(
            model_name='diatreball',
            name='hores_ajustades',
            field=models.BooleanField(blank=True, default=False, verbose_name='Hores ja ajustades a la jornada'),
        ),
        migrations.AlterField(
            model_name='diatreball',
            name='hores_restants',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Hores Restants'),
        ),
        migrations.AlterField(
            model_name='diatreball',
            name='hores_totals',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Hores Treballades'),
        ),
        migrations.AlterField(
            model_name='diatreball',
            name='nova_jornada_diaria',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Jornada Laboral Asignada'),
        ),
    ]
