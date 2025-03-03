from datetime import timedelta
from contextlib import nullcontext as does_not_raise

import pytest
from django.core.exceptions import ValidationError

from fitness.models import WorkoutExercise, ActivityThumbnail, Set


@pytest.mark.parametrize(
    'time, reps, until_failure, expected_existence, expected_exception', [
        pytest.param(
            None,
            None,
            True,
            True,
            does_not_raise(),
            id='until-failure-true'
        ),
        pytest.param(
            timedelta(minutes=2),
            None,
            False,
            True,
            does_not_raise(),
            id='time-populated'
        ),
        pytest.param(
            None,
            8,
            False,
            True,
            does_not_raise(),
            id='reps-populated'
        ),
        pytest.param(
            None,
            8,
            True,
            False,
            pytest.raises(ValidationError, match='until_failure cannot be selected whilst having reps/time set.'),
            id='reps-and-until-failure'
        ),
        pytest.param(
            timedelta(minutes=2),
            None,
            True,
            False,
            pytest.raises(ValidationError, match='until_failure cannot be selected whilst having reps/time set.'),
            id='time-and-until-failure'
        ),
        pytest.param(
            timedelta(minutes=2),
            8,
            True,
            False,
            pytest.raises(ValidationError, match='until_failure cannot be selected whilst having reps/time set.'),
            id='time-reps-and-until-failure'
        ),
        pytest.param(
            timedelta(minutes=2),
            8,
            False,
            False,
            pytest.raises(ValidationError, match='time and reps cannot both be set.'),
            id='time-and-reps'
        )
    ]
)
def test_workoutexercise_field_conflicts(time, reps, until_failure, expected_existence, expected_exception,
                                         exercise, workout, db):
    workout_exercise = WorkoutExercise.objects.create(
        workout=workout,
        exercise=exercise
    )

    with expected_exception:
        Set.objects.create(
            workout_exercise=workout_exercise,
            time=time,
            reps=reps,
            until_failure=until_failure
        )

    assert Set.objects.filter(workout_exercise=workout_exercise).exists() is expected_existence


@pytest.mark.parametrize(
    'name', [
        pytest.param(
            'some name',
            id='given-name'
        ),
        pytest.param(
            None,
            id='no-given-name'
        )
    ]
)
def test_activitythumbnail_name_autocreation(name, db):
    ActivityThumbnail.objects.create(
        name=name,
        image_file='test.png'
    )

    assert ActivityThumbnail.objects.filter(name__exact='test').exists()
