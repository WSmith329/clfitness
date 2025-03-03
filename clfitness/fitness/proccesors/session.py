import re

from django.core.exceptions import ValidationError

from fitness.models import WorkoutSession, SessionExercise


class SessionInputProcessor:
    INPUT_REGEX = re.compile(r'^(?P<we_id>\d+)-(?P<order>\d+)-(?P<field>reps|weight)$')

    def __init__(self, workout, client, inputs) -> None:
        self.workout = workout
        self.client = client
        self.inputs = inputs

        self.session = WorkoutSession.objects.create(
            workout=workout,
            completed_by=client
        )

        super().__init__()

    def _extract_set_recordings(self, workout_exercise):
        set_recordings = []
        for name, value in self.inputs:
            if (match := self.INPUT_REGEX.match(name)) and match.group('we_id') == str(workout_exercise.id):
                order = int(match.group('order'))
                field = match.group('field')

                exercise_set = workout_exercise.set_set.get(order__exact=order)
                aim = exercise_set.reps if exercise_set.reps else exercise_set.time

                current_set = next((rec for rec in set_recordings if rec['order'] == order), None)
                if current_set is None:
                    current_set = {'order': order}
                    set_recordings.append(current_set)

                if field == 'reps':
                    current_set['completed'] = int(value)
                else:
                    current_set[field] = int(value)
                current_set['aim'] = aim
        return set_recordings

    def _create_session_exercise(self, workout_exercise, set_recordings):
        expected_number_of_sets = len(workout_exercise.set_set.all())
        given_number_of_sets = len(set_recordings)

        if given_number_of_sets == expected_number_of_sets:
            SessionExercise.objects.create(
                session=self.session,
                workout_exercise=workout_exercise,
                set_recordings=set_recordings
            )
        else:
            raise ValidationError(f"Expected {expected_number_of_sets} sets, but received {given_number_of_sets} sets.")

    def process(self):
        for workout_exercise in self.workout.workoutexercise_set.all():
            set_recordings = self._extract_set_recordings(workout_exercise)
            self._create_session_exercise(workout_exercise, set_recordings)
