# Generated by Django 2.2.3 on 2019-07-09 22:43

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Marcatge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entrada', models.DateTimeField()),
                ('sortida', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Treballador',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=200)),
                ('vat', models.CharField(max_length=20)),
            ],
        ),
    ]