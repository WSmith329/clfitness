import pytest

from contextlib import nullcontext as does_not_raise
from django.core.exceptions import ValidationError
from unittest.mock import Mock, call

from fitness.models import Set, SessionExercise, WorkoutExercise
from fitness.proccesors.session import SessionInputProcessor


@pytest.fixture
def session_input_processor(workout, client_user, db):
    return SessionInputProcessor(
        workout=workout,
        client=client_user.client,
        inputs={}
    )


def test_extract_set_recordings(session_input_processor, workout_exercise):
    for order, reps in enumerate([8, 8]):
        Set.objects.create(
            workout_exercise=workout_exercise,
            order=order + 1,
            reps=reps
        )

    session_input_processor.inputs = [
        (f'{workout_exercise.id}-1-reps', '9'),
        (f'{workout_exercise.id}-1-weight', '20'),
        (f'{workout_exercise.id}-2-reps', '7'),
        (f'{workout_exercise.id}-2-weight', '22'),
        ('not-a-session-exercise', 'something')
    ]

    expected_recordings = [
        {
            'order': 1,
            'aim': 8,
            'completed': 9,
            'weight': 20
        },
        {
            'order': 2,
            'aim': 8,
            'completed': 7,
            'weight': 22
        }
    ]

    returned_recordings = session_input_processor._extract_set_recordings(workout_exercise)

    assert expected_recordings == returned_recordings


@pytest.mark.parametrize(
    'set_recordings, expected_existence, expected_raise', [
        pytest.param([
            {
                'order': 1,
                'aim': 8,
                'completed': 9,
                'weight': 20
            },
            {
                'order': 2,
                'aim': 8,
                'completed': 7,
                'weight': 22
            }],
            True,
            does_not_raise(),
            id='expected_number_of_sets'
        ),
        pytest.param([
            {
                'order': 1,
                'aim': 8,
                'completed': 9,
                'weight': 20
            }],
            False,
            pytest.raises(ValidationError, match='Expected 2 sets, but received 1 sets.'),
            id='unexpected_number_of_sets'
        )
    ]
)
def test_create_session_exercise(set_recordings, expected_existence, expected_raise,
                                 session_input_processor, workout_exercise):
    for order, reps in enumerate([8, 8]):
        Set.objects.create(
            workout_exercise=workout_exercise,
            order=order + 1,
            reps=reps
        )

    with expected_raise:
        session_input_processor._create_session_exercise(workout_exercise, set_recordings)

        assert SessionExercise.objects.filter(
            session=session_input_processor.session,
            workout_exercise=workout_exercise,
            set_recordings=set_recordings
        ).exists() == expected_existence


def test_process(session_input_processor, exercise, monkeypatch):
    workout_exercises = []
    for order in [1, 2]:
        workout_exercise = WorkoutExercise.objects.create(
            workout=session_input_processor.workout,
            exercise=exercise,
            order=order,
        )
        workout_exercises.append(workout_exercise)

    mock_extract_set_recordings = Mock()
    mock_create_session_exercise = Mock()

    monkeypatch.setattr(
        'fitness.proccesors.session.SessionInputProcessor._extract_set_recordings',
        mock_extract_set_recordings
    )
    monkeypatch.setattr(
        'fitness.proccesors.session.SessionInputProcessor._create_session_exercise',
        mock_create_session_exercise
    )

    session_input_processor.process()

    assert mock_extract_set_recordings.call_count == 2
    assert mock_create_session_exercise.call_count == 2

    expected_args = [
        call(workout_exercise, mock_extract_set_recordings.return_value)
        for workout_exercise in WorkoutExercise.objects.all()
    ]
    mock_create_session_exercise.assert_has_calls(expected_args, any_order=True)
