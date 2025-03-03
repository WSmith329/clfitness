import pytest
from django.test import Client
from django.urls import reverse

from fitness.models import WorkoutSession


@pytest.mark.parametrize(
    'existing_session, status_code', [
        pytest.param(
            True,
            200,
            id='existing-session'
        ),
        pytest.param(
            False,
            404,
            id='non-existing-session'
        )
    ]
)
def test_completed_session_get(existing_session, status_code, client_user, workout, request):
    client = Client()
    client.force_login(client_user)

    if existing_session:
        session = request.getfixturevalue('workout_session')
    else:
        session = WorkoutSession(id=1, workout=workout, completed_by=client_user.client)

    response = client.get(reverse('completed_session', args=[session.id]))

    if existing_session:
        assert response.status_code == 200
        assert response.context['user'] == client_user
        assert response.context['session'] == session
    else:
        assert response.status_code == 404
