# import pytest
#
# from django.urls import reverse
# from pytest_django.asserts import assertQuerySetEqual
#
#
# def test_recorded_workouts_get(client_user_client, workout_session, db):
#     response = client_user_client.get(reverse('recorded_workouts'))
#
#     assert response.status_code == 200
#     assert response.context['user'] == workout_session.completed_by.user
#     assertQuerySetEqual(response.conb'text['history'], [repr(workout_session)], transform=repr)
