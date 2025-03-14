# Generated by Django 5.0.1 on 2025-02-27 22:31

import django.db.models.deletion
import django_jsonform.models.fields
import phonenumber_field.modelfields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Service',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sex', models.CharField(choices=[('UN', 'Unspecified'), ('MR', 'Male'), ('MS', 'Female'), ('MX', 'Intersex')], default='UN', max_length=2)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, region=None)),
                ('since', models.DateField(blank=True, null=True)),
                ('until', models.DateField(blank=True, null=True)),
                ('personal_information', models.TextField(blank=True)),
                ('health_and_fitness_notes', models.TextField(blank=True)),
                ('aims', django_jsonform.models.fields.JSONField(blank=True, null=True)),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user'],
            },
        ),
        migrations.CreateModel(
            name='MeasurementRecording',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weight', models.DecimalField(decimal_places=2, help_text='kg', max_digits=5)),
                ('height', models.DecimalField(decimal_places=2, help_text='m', max_digits=3)),
                ('body_fat', models.DecimalField(decimal_places=2, help_text='%', max_digits=5)),
                ('bmi', models.DecimalField(decimal_places=2, max_digits=4)),
                ('recorded', models.DateField()),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_management.client')),
            ],
            options={
                'ordering': ['recorded'],
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_code', models.CharField(blank=True, help_text='Auto-generated. Only input manually when necessary.', max_length=10, unique=True)),
                ('amount_due', models.PositiveSmallIntegerField(default=0)),
                ('amount_paid', models.PositiveSmallIntegerField(default=0)),
                ('due_date', models.DateField()),
                ('requested_date', models.DateField(blank=True, editable=False, null=True)),
                ('completed_date', models.DateField(blank=True, editable=False, null=True)),
                ('status', models.CharField(choices=[('DR', 'Draft'), ('RE', 'Requested'), ('CO', 'Completed'), ('VO', 'Void')], default='DR', editable=False, max_length=2)),
                ('notes', models.TextField(blank=True, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_management.client')),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weeks', models.PositiveSmallIntegerField(blank=True, default=4, null=True)),
                ('sessions', models.PositiveSmallIntegerField(blank=True, default=1, null=True)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_management.payment')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='client_management.service')),
            ],
        ),
        migrations.AddField(
            model_name='payment',
            name='services',
            field=models.ManyToManyField(through='client_management.Subscription', to='client_management.service'),
        ),
    ]
