import datetime
from unittest.mock import Mock

import freezegun
import pytest
from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.urls import reverse

from client_management.forms import CompletedDateForm
from client_management.models import Payment


def test_mark_as_completed_get(requested_payment, admin_user_client):
    response = admin_user_client.get(
        reverse('admin:client_management_payment_mark_as_completed', args=[requested_payment.pk])
    )
    assert response.status_code == 200
    assert isinstance(response.context_data['form'], CompletedDateForm)


@freezegun.freeze_time(datetime.date(2025, 2, 25))
@pytest.mark.parametrize(
    'amount_paid, post_data, expected_http_code, expected_completed_date, expected_status, expected_message',
    [
        pytest.param(
            120,
            {},
            302,
            datetime.date(2025, 2, 25),
            Payment.PaymentStatuses.COMPLETED.value,
            'Payment successfully marked as completed.',
            id='blank_form'
        ),
        pytest.param(
            120,
            {'completed_date': datetime.date(2025, 2, 20)},
            302,
            datetime.date(2025, 2, 20),
            Payment.PaymentStatuses.COMPLETED.value,
            'Payment successfully marked as completed.',
            id='specify_date'
        ),
        pytest.param(
            100,
            {'ignore_unpaid': True},
            302,
            datetime.date(2025, 2, 25),
            Payment.PaymentStatuses.COMPLETED.value,
            'Payment successfully marked as completed.',
            id='ignore_unpaid'
        ),
        pytest.param(
            100,
            {},
            302,
            None,
            Payment.PaymentStatuses.REQUESTED.value,
            'Marking payment as completed failed as "amount paid" does not match "amount due".',
            id='unpaid_not_ignored'
        ),
        pytest.param(
            120,
            {'completed_date': 'not a datetime'},
            200,
            None,
            Payment.PaymentStatuses.REQUESTED.value,
            None,
            id='invalid_form'
        )
    ]
)
def test_mark_as_completed_post(amount_paid, post_data, expected_http_code, expected_completed_date, expected_status,
                                expected_message, requested_payment, admin_user_client):
    requested_payment.amount_paid = amount_paid  # alter whether amount paid aligns with amount due
    requested_payment.save()

    response = admin_user_client.post(
        reverse('admin:client_management_payment_mark_as_completed', args=[requested_payment.pk]),
        data=post_data
    )
    assert response.status_code == expected_http_code

    if response.status_code == 200:  # if form is valid, the response will be a redirect (302)
        assert response.context_data['form'].is_valid() is False

    if expected_message:
        message = messages.get_messages(response.wsgi_request)._queued_messages[0].message
        assert message == expected_message

    requested_payment.refresh_from_db()
    assert requested_payment.status == expected_status
    assert requested_payment.completed_date == expected_completed_date


@freezegun.freeze_time(datetime.date(2025, 2, 25))
def test_send_payment_request_success(payment, admin_user_client, mailoutbox):
    assert len(mailoutbox) == 0

    response = admin_user_client.post(
        reverse('admin:client_management_payment_send_payment_request', args=[payment.pk])
    )
    assert response.status_code == 302
    assert len(mailoutbox) == 1

    message = messages.get_messages(response.wsgi_request)._queued_messages[0].message
    assert message == 'Payment requested, email sent to user@testmail.com.'

    payment.refresh_from_db()
    assert payment.is_requested
    assert payment.requested_date == datetime.date(2025, 2, 25)


def test_send_payment_request_error(payment, admin_user_client, mailoutbox, monkeypatch):
    assert len(mailoutbox) == 0

    monkeypatch.setattr(
        'client_management.controllers.payment.PaymentRequestHandler.generate_payment_invoice_pdf',
        Mock(return_value=None)
    )

    response = admin_user_client.post(
        reverse('admin:client_management_payment_send_payment_request', args=[payment.pk])
    )
    assert response.status_code == 302
    assert len(mailoutbox) == 0

    message = messages.get_messages(response.wsgi_request)._queued_messages[0].message
    assert message == 'Payment request failed due to an internal server error.'

    assert payment.is_draft
    assert not payment.requested_date


@freezegun.freeze_time(datetime.datetime(2025, 2, 25, 12, 30, 0, 0))
def test_export_to_google_sheets_success(payment, admin_user_client, monkeypatch):
    monkeypatch.setattr(
        'client_management.controllers.google_sheets.GoogleSheetsClient.__init__',
        Mock(return_value=None)
    )

    create_sheet_from_dataframe_mock = Mock(return_value=None)
    monkeypatch.setattr(
        'client_management.controllers.google_sheets.GoogleSheetsClient.create_sheet_from_dataframe',
        create_sheet_from_dataframe_mock
    )

    response = admin_user_client.post(
        reverse('admin:client_management_payment_changelist'),
        {
            'action': 'export_to_google_sheets',
            ACTION_CHECKBOX_NAME: [str(payment.pk)]
        }
    )
    assert response.status_code == 302

    message = messages.get_messages(response.wsgi_request)._queued_messages[0].message
    assert message == 'Google Sheet created and populated with selected payments.'

    create_sheet_from_dataframe_mock.assert_called_once()
    assert create_sheet_from_dataframe_mock.call_args[0][1] == 'Invoices-2025-02-25-12:30:00'


@freezegun.freeze_time(datetime.datetime(2025, 2, 25, 12, 30, 0, 0))
def test_export_to_google_sheets_failure(payment, admin_user_client, monkeypatch):
    monkeypatch.setattr(
        'client_management.controllers.google_sheets.GoogleSheetsClient.__init__',
        Mock(side_effect=Exception)
    )

    response = admin_user_client.post(
        reverse('admin:client_management_payment_changelist'),
        {
            'action': 'export_to_google_sheets',
            ACTION_CHECKBOX_NAME: [str(payment.pk)]
        }
    )
    assert response.status_code == 302

    message = messages.get_messages(response.wsgi_request)._queued_messages[0].message
    assert message == 'An error occurred whilst generating the Google Sheet.'
