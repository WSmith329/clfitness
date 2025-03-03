import datetime
import io
import os

import gspread
import numpy as np
import pandas as pd
import pytz
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.mail import EmailMessage
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from django.template.loader import render_to_string
from weasyprint import HTML

from client_management.controllers.google_sheets import GoogleSheetsClient
from client_management.models import Payment


class PaymentSheetGenerator:
    MAPPING = {
        'Client': 'client__user__first_name',
        'Number': 'invoice_code',
        'Date sent': 'requested_date',
        'Amount': 'amount_due',
        'What for': 'what_for',
        'Date due': 'due_date',
        # 'Paid' column isn't populated using Django model field
        'Date paid': 'completed_date',
    }

    ORDERED_HEADERS = [
        'Client', 'Number', 'Date sent', 'Amount', 'What for', 'Date due', 'Paid', 'Date paid'
    ]

    DATE_COLUMNS = ['Date sent', 'Date due', 'Date paid']

    def _construct_dataframe(self, payments):
        df = pd.DataFrame.from_records(payments)

        df.rename(columns={field: header for header, field in self.MAPPING.items()}, inplace=True)

        df = self._transform_dataframe(df)

        df = df[self.ORDERED_HEADERS]

        return df

    def _transform_dataframe(self, df):
        df['Paid'] = df.apply(lambda p: 'yes' if p['Date paid'] else 'no', axis=1)
        df['What for'] = df['What for'].apply(lambda p: ', '.join(map(str, p)))
        df = self._format_dates(df)
        df = df.fillna(np.nan)
        return df

    def generate(self, payments):
        payments = payments.annotate(
            what_for=ArrayAgg(
                Concat('subscription__weeks', Value(' weeks x '), 'subscription__sessions', Value(' sessions of '), 'services__name', output_field=CharField()),
                distinct=True
            )
        ).order_by('completed_date')
        payments = list(payments.values(*self.MAPPING.values()))

        df = self._construct_dataframe(payments)

        sheet_name = f'Invoices-{datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")}'

        GoogleSheetsClient().create_sheet_from_dataframe(df, sheet_name)

    def _format_dates(self, df):
        for col in self.DATE_COLUMNS:
            df[col] = pd.to_datetime(df[col])
            df[col] = df[col].dt.strftime('%d/%m/%Y')
        return df


class PaymentRequestHandler:
    PAYMENT_EMAIL_TEMPLATE = 'client_management/payment_email.html'
    PAYMENT_INVOICE_TEMPLATE = 'client_management/payment_invoice.html'

    def __init__(self, pk):
        self.payment = Payment.objects.get(pk=pk)
        self.client = self.payment.client
        self.context = self._build_template_context()

    def _build_template_context(self):
        return {
            'invoice': self.payment.invoice_code,
            'due_date': self.payment.due_date.strftime('%e %B %Y'),
            'amount_due': self.payment.amount_due,
            'client_name': self.client.user.first_name,
            'services': ', '.join(f'{subscription.service.name} for {subscription.weeks} weeks'
                                  for subscription in self.payment.subscription_set.all())
        }

    def send_payment_request(self) -> None:
        pdf_buffer = self.generate_payment_invoice_pdf()

        subject = 'PT Invoice'
        body = render_to_string(self.PAYMENT_EMAIL_TEMPLATE, self.context)
        from_email = settings.EMAIL_HOST_USER
        to_email = [self.client.user.email]

        email = EmailMessage(subject, body, from_email, to_email)
        email.attach(f'Invoice {self.client.user.first_name} {self.payment.invoice_code}.pdf',
                     pdf_buffer.read(), 'application/pdf')
        email.content_subtype = 'html'

        email.send()

        pdf_buffer.close()

    def generate_payment_invoice_pdf(self) -> io.BytesIO:
        html_content = render_to_string(self.PAYMENT_INVOICE_TEMPLATE, self.context)

        pdf_buffer = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)
        return pdf_buffer
