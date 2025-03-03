import logging

from admin_extra_buttons.decorators import button
from admin_extra_buttons.mixins import ExtraButtonsMixin
from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.combo import ChoicesFieldComboFilter
from adminfilters.mixin import AdminFiltersMixin
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.templatetags.admin_urls import admin_urlname
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter, NumericRangeFilter

from client_management.controllers.payment import PaymentSheetGenerator
from client_management.forms import CompletedDateForm
from client_management.models import Client, MeasurementRecording, Payment, Subscription, Service

logger = logging.getLogger(__name__)


class ClientStatusFilter(admin.SimpleListFilter):
    title = 'Client Status'
    parameter_name = 'client_status'

    def lookups(self, request, model_admin):
        return (
            ('is_client', _('Yes')),
            ('not_client', _('No'))
        )

    def queryset(self, request, queryset):
        match self.value():
            case 'is_client':
                return queryset.filter(client__isnull=False)
            case 'not_client':
                return queryset.filter(client__isnull=True)
            case _:
                return queryset


class ClientInline(admin.StackedInline):
    model = Client
    can_delete = False


class UserAdmin(BaseUserAdmin):
    def client_status(self, obj):
        try:
            return obj.client is not None
        except Client.DoesNotExist:
            return False

    client_status.boolean = True

    list_display = BaseUserAdmin.list_display + ('client_status',)
    list_filter = BaseUserAdmin.list_filter + (ClientStatusFilter,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'since', 'until')
    search_fields = ('user', )
    list_filter = (
        ('since', DateRangeFilter),
        ('until', DateRangeFilter),
    )


@admin.register(MeasurementRecording)
class MeasurementRecordingAdmin(admin.ModelAdmin):
    list_display = ('client', 'weight', 'height', 'body_fat', 'bmi')
    search_fields = ('client',)
    list_filter = (
        ('weight', NumericRangeFilter),
        ('height', NumericRangeFilter),
        ('body_fat', NumericRangeFilter),
        ('bmi', NumericRangeFilter),
        ('recorded', DateRangeFilter),
    )


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    min_num = 1
    extra = 1


@admin.register(Payment)
class PaymentAdmin(AdminFiltersMixin, ExtraButtonsMixin, admin.ModelAdmin):
    list_display = ('invoice_code', 'client', 'amount_due', 'amount_paid', 'requested_date', 'completed_date', 'status')
    list_filter = (
        ('client', AutoCompleteFilter),
        ('status', ChoicesFieldComboFilter),
        ('services', AutoCompleteFilter),
        ('due_date', DateRangeFilter),
        ('requested_date', DateRangeFilter),
        ('completed_date', DateRangeFilter)
    )
    inlines = (SubscriptionInline,)
    readonly_fields = ('status', 'requested_date', 'completed_date')
    actions = ('export_to_google_sheets',)

    @admin.action(description=_('Export to Google Sheets'))
    def export_to_google_sheets(self, request, queryset):
        try:
            PaymentSheetGenerator().generate(queryset)
        except Exception as e:
            messages.error(request, 'An error occurred whilst generating the Google Sheet.')
        else:
            messages.success(request, 'Google Sheet created and populated with selected payments.')

    @button(change_form=True, visible=lambda btn: btn.original.status == Payment.PaymentStatuses.DRAFT.value)
    def send_payment_request(self, request, pk):
        payment = Payment.objects.get(pk=pk)
        try:
            payment.request()
        except Exception as e:
            messages.error(request, 'Payment request failed due to an internal server error.')
        else:
            messages.success(request, f'Payment requested, email sent to {payment.client.user.email}.')

    @button(change_form=True, visible=lambda btn: btn.original.status == Payment.PaymentStatuses.REQUESTED.value)
    def mark_as_completed(self, request, pk):
        context = self.get_common_context(request, title='Mark Payment as Completed')
        if request.method == 'POST':
            form = CompletedDateForm(request.POST)
            if form.is_valid():
                payment = Payment.objects.get(pk=pk)
                if payment.amount_due == payment.amount_paid or form.cleaned_data['ignore_unpaid']:
                    payment.completed_date = form.cleaned_data['completed_date']
                    payment.set_as_completed(auto_today=not bool(payment.completed_date))
                    messages.success(request, 'Payment successfully marked as completed.')
                else:
                    messages.error(
                        request,
                        'Marking payment as completed failed as "amount paid" does not match "amount due".'
                    )
                return redirect(reverse(admin_urlname(context['opts'], 'change'), args=[pk]))
        else:
            form = CompletedDateForm()
        context['form'] = form
        return TemplateResponse(request, 'client_management/admin_extra_button_form.html', context)


@admin.register(Service)
class ServiceAdmin(AdminFiltersMixin, admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name',)
