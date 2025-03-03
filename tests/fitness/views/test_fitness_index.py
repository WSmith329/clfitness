import pytest

from django.urls import reverse
from pytest_django.asserts import assertQuerySetEqual


@pytest.mark.parametrize('workout_fixtures, django_client', [
    pytest.param(('workout_plan', 'workout_session'), 'client_user_client', id='with_workouts'),
    pytest.param(None, 'client_user_client', id='without_workouts'),
    pytest.param(('workout_plan', 'workout_session'), 'admin_user_client', id='non_client_user')
])
def test_index_get(workout_fixtures, django_client, request, db):
    if workout_fixtures:
        workout_plan = request.getfixturevalue(workout_fixtures[0])
        workout_session = request.getfixturevalue(workout_fixtures[1])

    django_client = request.getfixturevalue(django_client)

    response = django_client.get(reverse('index'))

    assert response.status_code == 200

    if workout_fixtures and response.context['user'] is workout_plan.client.user:
        assert response.context['user'] == workout_plan.client.user

        assertQuerySetEqual(response.context['plans'], [repr(workout_plan)], transform=repr)
        assertQuerySetEqual(response.context['history'], [repr(workout_session)], transform=repr)