import datetime

from django.test import Client
from django.urls import reverse

from config.factories.fitness import WorkoutFactory
from fitness.models import WorkoutSession


def test_completed_chart(client_user, request):
    client = Client()
    client.force_login(client_user)

    sessions = []
    for s in range(20):
        sessions.append(
            WorkoutSession(workout=WorkoutFactory(), completed_by=client_user.client)
        )
    WorkoutSession.objects.bulk_create(sessions)
    for i, s in enumerate(sessions):
        session_date = datetime.datetime.now() + datetime.timedelta(days=(i+1)*2)
        s.completed_on = session_date
    WorkoutSession.objects.bulk_update(sessions, ['completed_on'])

    response = client.get(reverse(viewname='completed_chart'))

    assert response.status_code == 200
    assert response.templates[0].name == 'fitness/completed_sessions_chart.html'
