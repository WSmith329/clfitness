import pytest
from constance.test import override_config

from config.factories.client_management import PaymentFactory


@pytest.fixture
def payment(business_client, db):
    with override_config(STARTING_INVOICE_NUMBER=12):
        return PaymentFactory(
            client=business_client
        )


@pytest.fixture
def requested_payment(payment):
    payment.amount_due = 120
    payment.set_as_requested()
    return payment
