# Generated by Django 2.2.3 on 2019-07-11 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marcatge', '0003_auto_20190709_2309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='marcatge',
            name='sortida',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
