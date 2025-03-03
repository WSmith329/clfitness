import datetime

from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = [
    path('', login_required(views.index), name='index'),
    path('all_workouts/', login_required(views.all_workouts), name='all_workouts'),
    path('workout/<str:workout_slug>/', login_required(views.workout), name='workout'),
    path('history/<int:session_id>', login_required(views.completed_session), name='completed_session'),
    path('completed_chart/', login_required(views.completed_chart), name='completed_chart'),
    path('calendar/<int:year>/<int:month>', login_required(views.monthly_calendar), name='calendar'),
    path(f'calendar/{datetime.datetime.today().year}/{datetime.datetime.today().month}', login_required(views.monthly_calendar), name='default_calendar'),
    path(f'calendar/<int:year>/<int:month>/<int:user_id>', login_required(views.monthly_calendar), name='user_calendar'),
]
