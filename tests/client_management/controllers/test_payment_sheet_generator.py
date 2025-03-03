import datetime
from unittest.mock import Mock

import freezegun
import numpy as np
import pandas as pd
import pytest

from client_management.controllers.payment import PaymentSheetGenerator
from client_management.models import Payment


@pytest.fixture
def payment_sheet_generator():
    return PaymentSheetGenerator()


@pytest.fixture
def expected_generated_dataframe(payment):
    return pd.DataFrame({
        'Client': ['Test'],
        'Number': ['INV00012'],
        'Date sent': [np.nan],
        'Amount': [0],
        'What for': [' weeks x  sessions of '],
        'Date due': [payment.due_date.strftime('%d/%m/%Y')],
        'Paid': ['no'],
        'Date paid': [np.nan]
    })


@freezegun.freeze_time(datetime.datetime(2025, 2, 25, 12, 30, 0, 0))
def test_generate(payment_sheet_generator, expected_generated_dataframe, monkeypatch):
    monkeypatch.setattr(
        'client_management.controllers.google_sheets.GoogleSheetsClient.__init__',
        Mock(return_value=None)
    )

    create_sheet_from_dataframe_mock = Mock(return_value=None)
    monkeypatch.setattr(
        'client_management.controllers.google_sheets.GoogleSheetsClient.create_sheet_from_dataframe',
        create_sheet_from_dataframe_mock
    )

    payments = Payment.objects.all()
    payment_sheet_generator.generate(payments)

    create_sheet_from_dataframe_mock.assert_called_once()
    assert create_sheet_from_dataframe_mock.call_args[0][0].compare(
        expected_generated_dataframe.fillna(np.nan)
    ).empty
    assert create_sheet_from_dataframe_mock.call_args[0][1] == 'Invoices-2025-02-25-12:30:00'
