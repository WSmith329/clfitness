import factory.django

from fitness.models import AbstractActivity, Workout, Exercise, WorkoutExercise


class ActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AbstractActivity

    name = factory.Sequence(lambda n: 'Test Activity %s' % n)
    slug = factory.Sequence(lambda n: 'test_activity %s' % n)


class ExerciseFactory(ActivityFactory):
    class Meta:
        model = Exercise

    instructions = {}


class WorkoutFactory(ActivityFactory):
    class Meta:
        model = Workout


class WorkoutExerciseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkoutExercise

    exercise = factory.SubFactory(ExerciseFactory)
    workout = factory.SubFactory(WorkoutFactory)
