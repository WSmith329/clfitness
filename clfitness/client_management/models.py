import datetime
import logging
from constance import config
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import IntegerField
from django.db.models.functions import Cast, Substr
from django.utils.translation import gettext_lazy as _
from django_jsonform.models.fields import JSONField
from phonenumber_field.modelfields import PhoneNumberField

logger = logging.getLogger(__name__)


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    class Sexes(models.TextChoices):
        UNSPECIFIED = 'UN', _('Unspecified')
        MALE = 'MR', _('Male')
        FEMALE = 'MS', _('Female')
        INTERSEX = 'MX', _('Intersex')
    sex = models.CharField(
        choices=Sexes,
        default=Sexes.UNSPECIFIED,
        max_length=2
    )

    phone_number = PhoneNumberField(blank=True)

    since = models.DateField(blank=True, null=True)
    until = models.DateField(blank=True, null=True)

    personal_information = models.TextField(blank=True)
    health_and_fitness_notes = models.TextField(blank=True)

    AIMS_SCHEMA = {
        'type': 'array',
        'title': 'Aims',
        'description': 'Add the aims of the client',
        'items': {
            'type': 'string',
            'widget': 'textarea'
        },
        'minItems': 0,
        'maxItems': 10
    }
    aims = JSONField(schema=AIMS_SCHEMA, blank=True, null=True)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return f'{self.user.username}'

    def clean(self):
        super().clean()
        if self.user and not self.user.email:
            raise ValidationError("Email is required for users that are clients.")
        if self.user and not self.user.first_name:
            raise ValidationError("First Name is required for users that are clients.")


class MeasurementRecording(models.Model):
    client = models.ForeignKey('Client', on_delete=models.CASCADE)

    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text='kg')
    height = models.DecimalField(max_digits=3, decimal_places=2, help_text='m')

    body_fat = models.DecimalField(max_digits=5, decimal_places=2, help_text='%')
    bmi = models.DecimalField(max_digits=4, decimal_places=2)

    recorded = models.DateField()

    class Meta:
        ordering = ['recorded']

    def __str__(self):
        return f'{self.client.user.username} ({self.recorded})'


class Service(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Payment(models.Model):
    invoice_code = models.CharField(
        max_length=10, unique=True, blank=True,
        help_text='Auto-generated. Only input manually when necessary.'
    )

    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    amount_due = models.PositiveSmallIntegerField(default=0)
    amount_paid = models.PositiveSmallIntegerField(default=0)

    due_date = models.DateField()
    requested_date = models.DateField(null=True, blank=True, editable=False)
    completed_date = models.DateField(null=True, blank=True, editable=False)

    services = models.ManyToManyField(Service, through='Subscription')

    class PaymentStatuses(models.TextChoices):
        DRAFT = 'DR', _('Draft')
        REQUESTED = 'RE', _('Requested')
        COMPLETED = 'CO', _('Completed')
        VOID = 'VO', _('Void')

    status = models.CharField(
        choices=PaymentStatuses,
        default=PaymentStatuses.DRAFT,
        max_length=2,
        editable=False
    )

    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.client.user.username} {self.requested_date}'

    def save(self, *args, **kwargs):
        if not self.invoice_code:
            self.invoice_code = self._generate_invoice_code()

        super().save(*args, **kwargs)

    @staticmethod
    def _generate_invoice_code():
        """Generate invoice code automatically."""
        prev_payment = Payment.objects.annotate(
            invoice_number=Cast(Substr('invoice_code', 4, 5), IntegerField())
        ).order_by('-invoice_number').first()
        if prev_payment:
            new_number = prev_payment.invoice_number + 1
        else:
            new_number = config.STARTING_INVOICE_NUMBER
        return f'INV{new_number:05d}'

    def request(self):
        try:
            from client_management.controllers.payment import PaymentRequestHandler
            PaymentRequestHandler(self.pk).send_payment_request()
        except Exception as e:
            logger.exception(e)
            raise e

        self.set_as_requested()

    def _set_status(self, target_status, valid_starting_statuses=None, date_field=None, save=True):
        if valid_starting_statuses is None:
            valid_starting_statuses = []
        if valid_starting_statuses and self.status not in valid_starting_statuses:
            logger.warning(f'Invalid status transition attempted: {self.status} -> {target_status}')
            raise ValueError(f'Cannot transition payment status from {self.status} to {target_status}.')
        self.status = target_status

        if date_field:
            setattr(self, date_field, datetime.date.today())

        if save:
            self.save()

    def set_as_requested(self):
        """Set payment status as requested."""
        self._set_status(
            self.PaymentStatuses.REQUESTED,
            [self.PaymentStatuses.DRAFT],
            'requested_date'
        )

    def set_as_completed(self, auto_today=True):
        """Set payment status as completed."""
        self._set_status(
            self.PaymentStatuses.COMPLETED,
            [self.PaymentStatuses.REQUESTED],
            'completed_date' if auto_today else None
        )

    def set_as_void(self):
        """Set payment status as void."""
        self._set_status(
            self.PaymentStatuses.VOID,
            [self.PaymentStatuses.DRAFT, self.PaymentStatuses.REQUESTED]
        )

    @property
    def is_draft(self):
        return self.status == self.PaymentStatuses.DRAFT

    @property
    def is_requested(self):
        return self.status == self.PaymentStatuses.REQUESTED

    @property
    def is_completed(self):
        return self.status == self.PaymentStatuses.COMPLETED

    @property
    def is_void(self):
        return self.status == self.PaymentStatuses.VOID


class Subscription(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    weeks = models.PositiveSmallIntegerField(null=True, blank=True, default=4)
    sessions = models.PositiveSmallIntegerField(null=True, blank=True, default=1)

    def __str__(self):
        return f'{self.payment.client} {self.service.name} {self.payment.requested_date}'
