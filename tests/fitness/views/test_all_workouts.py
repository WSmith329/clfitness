import pytest

from django.urls import reverse
from pytest_django.asserts import assertQuerySetEqual


def test_all_workouts_get(client_user_client, workout_plan, db):
    response = client_user_client.get(reverse('all_workouts'))

    assert response.status_code == 200
    assert response.context['user'] == workout_plan.client.user
    assertQuerySetEqual(response.context['plans'], [repr(workout_plan)], transform=repr)
