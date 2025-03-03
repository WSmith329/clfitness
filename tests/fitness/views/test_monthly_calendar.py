import datetime

import freezegun
import pytest

from django.urls import reverse
from pytest_django.asserts import assertQuerySetEqual


@freezegun.freeze_time(datetime.date(2025, 3, 1))
def test_monthly_calendar_get(client_user_client, workout_assignment_on_mondays, db):
    workout_assignment = workout_assignment_on_mondays
    workout_assignment.exact_dates = [
        datetime.date(2025, 3, 7),
        datetime.date(2025, 3, 20),
        datetime.date(2026, 3, 20)
    ]
    workout_assignment.save()

    response = client_user_client.get(reverse('calendar', args=[2025, 3]))

    assert response.status_code == 200
    assert response.context['user'] == workout_assignment.workout_plan.client.user
    assert response.context['weekdays'] == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert response.context['today'] == datetime.datetime.today()
    assert response.context['month_itinerary'] == [
        [(0, []), (0, []), (0, []), (0, []), (0, []), (1, []), (2, [])],
        [(3, [workout_assignment]), (4, []), (5, []), (6, []), (7, [workout_assignment]), (8, []), (9, [])],
        [(10, [workout_assignment]), (11, []), (12, []), (13, []), (14, []), (15, []), (16, [])],
        [(17, [workout_assignment]), (18, []), (19, []), (20, [workout_assignment]), (21, []), (22, []), (23, [])],
        [(24, [workout_assignment]), (25, []), (26, []), (27, []), (28, []), (29, []), (30, [])],
        [(31, [workout_assignment]), (0, []), (0, []), (0, []), (0, []), (0, []), (0, [])],
    ]
    assert response.context['this_month'] == datetime.datetime(2025, 3, 1)
    assert response.context['next_month'] == datetime.datetime(2025, 4, 1)
    assert response.context['last_month'] == datetime.datetime(2025, 2, 28)


@freezegun.freeze_time(datetime.date(2025, 3, 1))
def test_user_monthly_calendar_get(client_user_client, workout_assignment_on_mondays, db):
    workout_assignment = workout_assignment_on_mondays
    workout_assignment.exact_dates = [
        datetime.date(2025, 3, 7),
        datetime.date(2025, 3, 20),
        datetime.date(2026, 3, 20)
    ]
    workout_assignment.save()

    client_user = workout_assignment.workout_plan.client.user

    response = client_user_client.get(reverse('user_calendar', args=[2025, 3, client_user.id]))

    assert response.status_code == 200
    assert response.context['user'] == workout_assignment.workout_plan.client.user
    assert response.context['weekdays'] == ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    assert response.context['today'] == datetime.datetime.today()
    assert response.context['month_itinerary'] == [
        [(0, []), (0, []), (0, []), (0, []), (0, []), (1, []), (2, [])],
        [(3, [workout_assignment]), (4, []), (5, []), (6, []), (7, [workout_assignment]), (8, []), (9, [])],
        [(10, [workout_assignment]), (11, []), (12, []), (13, []), (14, []), (15, []), (16, [])],
        [(17, [workout_assignment]), (18, []), (19, []), (20, [workout_assignment]), (21, []), (22, []), (23, [])],
        [(24, [workout_assignment]), (25, []), (26, []), (27, []), (28, []), (29, []), (30, [])],
        [(31, [workout_assignment]), (0, []), (0, []), (0, []), (0, []), (0, []), (0, [])],
    ]
    assert response.context['this_month'] == datetime.datetime(2025, 3, 1)
    assert response.context['next_month'] == datetime.datetime(2025, 4, 1)
    assert response.context['last_month'] == datetime.datetime(2025, 2, 28)
