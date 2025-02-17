# Generated by Django 5.1.6 on 2025-02-08 18:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcatge', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiaTreball',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dia', models.DateField()),
                ('hores_totals', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('treballador', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marcatge.treballador')),
            ],
        ),
    ]
