import datetime

import freezegun
from django.urls import reverse

from client_management.models import MeasurementRecording


def test_measurement_recording_get(client_user_client):
    response = client_user_client.get(
        reverse('measurement_recording')
    )
    assert response.status_code == 200


@freezegun.freeze_time(datetime.date(2025, 2, 1))
def test_measurement_recording_post_success(client_user_client):
    response = client_user_client.post(
        reverse('measurement_recording'),
        data={'weight': 80, 'height': 1.8, 'body_fat': 30, 'bmi': 24.7},
        follow=True
    )
    assert response.status_code == 200
    assert MeasurementRecording.objects.get(
        client=response.wsgi_request.user.client,
        weight=80,
        height=1.8,
        body_fat=30,
        bmi=24.7,
        recorded=datetime.date.today()
    )


def test_measurement_recording_post_invalid(client_user_client):
    response = client_user_client.post(
        reverse('measurement_recording'),
        data={'weight': 80, 'height': 1.8, 'body_fat': 'invalid', 'bmi': 24.7},
    )
    assert response.status_code == 200
    assert b'Enter a number.' in response.content
    assert MeasurementRecording.objects.all().count() == 0
