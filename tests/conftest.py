import pytest
from django.test import Client as Django_Client
from factories.fitness import WorkoutFactory, ExerciseFactory

from client_management.models import Client
from fitness.models import WorkoutExercise, WorkoutSession, WorkoutPlan, WorkoutAssignment, Weekday, Steps, \
    CompletedSteps


@pytest.fixture
def admin_user(db, django_user_model):
    return django_user_model.objects.create_superuser(
        username='admin',
        password='admin_pass',
    )


@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='test_user',
        password='test_pass',
        email='user@testmail.com',
        first_name='Test'
    )


@pytest.fixture
def business_client(user):
    return Client.objects.create(
        user=user
    )


@pytest.fixture
def client_user(business_client):
    return business_client.user


@pytest.fixture
def user_password():
    return 'test_pass'


@pytest.fixture()
def admin_user_client(admin_user):
    client = Django_Client()
    client.force_login(admin_user)
    return client


@pytest.fixture()
def client_user_client(client_user):
    client = Django_Client()
    client.force_login(client_user)
    return client


@pytest.fixture
def workout(db):
    return WorkoutFactory()


@pytest.fixture
def exercise(db):
    return ExerciseFactory()


@pytest.fixture
def workout_exercise(workout, exercise, db):
    return WorkoutExercise.objects.create(
        workout=workout,
        exercise=exercise
    )


@pytest.fixture
def workout_session(workout, client_user, db):
    return WorkoutSession.objects.create(
        workout=workout,
        completed_by=client_user.client
    )


@pytest.fixture
def workout_plan(workout, client_user, db):
    return WorkoutPlan.objects.create(
        client=client_user.client
    )


@pytest.fixture
def workout_assignment_on_mondays(workout, workout_plan, db):
    return WorkoutAssignment.objects.create(
        workout=workout,
        workout_plan=workout_plan,
        weekday=[Weekday.MONDAY]
    )


@pytest.fixture
def steps_for_monday(client_user, db):
    return Steps.objects.create(
        amount=10000,
        weekday=[Weekday.MONDAY],
        client=client_user.client
    )


@pytest.fixture
def completed_steps(client_user, db):
    return CompletedSteps.objects.create(
        aim=10000,
        completed=12000,
        completed_by=client_user.client
    )
