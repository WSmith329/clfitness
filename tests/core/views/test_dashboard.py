import datetime

import freezegun
import pytest
from django.test import Client as Django_Client
from django.urls import reverse

from fitness.forms import CompletedStepsForm
from fitness.models import CompletedSteps


@freezegun.freeze_time(datetime.date(2025, 2, 24))
def test_dashboard_get(client_user_client, workout_assignment_on_mondays, steps_for_monday, completed_steps):
    workout_assignment = workout_assignment_on_mondays

    completed_steps.completed_on = datetime.date.today()
    completed_steps.save()

    response = client_user_client.get(
        reverse('dashboard')
    )
    assert response.status_code == 200
    assert response.context['title'] == str(workout_assignment.workout_plan.client)
    assert list(response.context['workout_assignments_today']) == [workout_assignment]
    assert response.context['steps_today'] == steps_for_monday
    assert response.context['steps_progress'] == 100
    assert isinstance(response.context['steps_form'], CompletedStepsForm)


@freezegun.freeze_time(datetime.date(2025, 2, 24))
def test_dashboard_get_with_no_steps(client_user_client, workout_assignment_on_mondays):
    workout_assignment = workout_assignment_on_mondays

    response = client_user_client.get(
        reverse('dashboard')
    )
    assert response.status_code == 200
    assert response.context['title'] == str(workout_assignment.workout_plan.client)
    assert list(response.context['workout_assignments_today']) == [workout_assignment]
    assert response.context['steps_today'] is None
    assert response.context['steps_progress'] == 0
    assert isinstance(response.context['steps_form'], CompletedStepsForm)


def test_dashboard_get_by_non_client(user):
    client = Django_Client()
    client.force_login(user)

    response = client.get(
        reverse('dashboard')
    )
    assert response.status_code == 200
    assert response.context['title'] == str(user)
    assert response.context['user'] == user


@freezegun.freeze_time(datetime.date(2025, 2, 24))
@pytest.mark.parametrize('completed_steps, expect_created', [
    pytest.param(5000, True, id='valid_form_values'),
    pytest.param('not valid int', False, id='invalid_form_values')
])
def test_dashboard_post(
        completed_steps, expect_created, client_user_client, workout_assignment_on_mondays, steps_for_monday
):
    workout_assignment = workout_assignment_on_mondays

    assert CompletedSteps.objects.count() == 0

    response = client_user_client.post(
        reverse('dashboard'),
        data={'completed': completed_steps},
        follow=True
    )
    assert response.status_code == 200
    assert response.context['title'] == str(workout_assignment.workout_plan.client)
    assert list(response.context['workout_assignments_today']) == [workout_assignment]
    assert response.context['steps_today'] == steps_for_monday
    assert isinstance(response.context['steps_form'], CompletedStepsForm)

    if expect_created:
        assert response.context['steps_progress'] == 50
        assert CompletedSteps.objects.get(
            aim=steps_for_monday.amount,
            completed=completed_steps,
            completed_by=workout_assignment.workout_plan.client,
            completed_on=datetime.date.today()
        )
    else:
        assert 'Enter a whole number.' in str(response.context['steps_form'].errors)
        assert response.context['steps_progress'] == 0
        assert CompletedSteps.objects.count() == 0
