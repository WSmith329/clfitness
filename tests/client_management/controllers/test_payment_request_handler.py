import datetime
import os
from pathlib import Path

import freezegun
import pytest
from constance import config
from constance.test import override_config
from django.utils.safestring import mark_safe


@pytest.fixture()
def sample_invoice_email_template():
    with open(os.path.join(Path(__file__).parent.parent, 'examples/sample_invoice_email.html'), 'r') as file:
        html = file.read()
    return mark_safe(html)


@freezegun.freeze_time(datetime.date(2025, 2, 26))
def test_send_payment_request(payment, sample_invoice_email_template, monkeypatch, mailoutbox):
    payment.due_date = datetime.date.today()
    payment.save()

    assert len(mailoutbox) == 0
    payment.request()
    assert len(mailoutbox) == 1

    attachments = mailoutbox[0].attachments
    assert len(attachments) == 1
    assert attachments[0][0] == 'Invoice Test INV00012.pdf'
    assert isinstance(attachments[0][1], bytes)
    assert attachments[0][2] == 'application/pdf'

    assert mailoutbox[0].content_subtype == 'html'
    assert mailoutbox[0].body == sample_invoice_email_template

    assert mailoutbox[0].subject == 'PT Invoice'
    assert mailoutbox[0].to == [payment.client.user.email]
