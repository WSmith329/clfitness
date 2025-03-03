from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from fitness.models import WorkoutSession, Workout, Set


@pytest.mark.parametrize(
    'existing_workout, status_code', [
        pytest.param(
            True,
            200,
            id='existing-workout'
        ),
        pytest.param(
            False,
            404,
            id='non-existing-workout'
        )
    ]
)
def test_workout_get(existing_workout, status_code, client_user, request):
    client = Client()
    client.force_login(client_user)

    if existing_workout:
        workout = request.getfixturevalue('workout')
    else:
        workout = Workout(name='Not A Workout', slug='not_a_workout')

    response = client.get(reverse('workout', args=[workout.slug]))

    if existing_workout:
        assert response.status_code == 200
        assert response.context['user'] == client_user
        assert response.context['workout'] == workout
    else:
        assert response.status_code == 404


@pytest.mark.parametrize(
    'form_inputs, number_of_sets, expected_exception', [
        pytest.param(
            {
                '1-1-reps': 9,
                '1-1-weight': 20,
                '1-2-reps': 7,
                '1-2-weight': 22,
                'not-a-session-exercise': 'something'
            },
            2,
            does_not_raise(),
            id='valid-data'
        ),
        pytest.param(
            {},
            2,
            pytest.raises(ValidationError, match='Expected 2 sets, but received 0 sets.'),
            id='invalid-input'
        ),
        pytest.param(
            {},
            0,
            does_not_raise(),
            id='empty-input'
        )
    ]
)
def test_workout_post(form_inputs, number_of_sets, expected_exception, workout_exercise, client_user):
    client = Client()
    client.force_login(client_user)

    workout_exercise.id = 1
    workout_exercise.save()

    for created_sets in range(int(number_of_sets)):
        Set.objects.create(
            workout_exercise=workout_exercise,
            order=created_sets+1,
            reps=8
        )

    with expected_exception:
        response = client.post(
            path=reverse('workout', args=[workout_exercise.workout.slug]),
            data=form_inputs
        )

        assert response.status_code == 302
        assert response.url == reverse('index')

    assert WorkoutSession.objects.filter(
        workout=workout_exercise.workout,
        completed_by=client_user.client
    ).exists()