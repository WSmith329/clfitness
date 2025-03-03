import calendar
import datetime
import re

import sentry_sdk
from django.contrib.auth.models import User
from django.db.models.functions import Trunc
from django.db.models import DateField
from django.http import HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect

from client_management.models import Client
from .models import Workout, SessionExercise, WorkoutSession, WorkoutPlan, WorkoutAssignment
from .proccesors.session import SessionInputProcessor


def index(request):
    current_user = request.user
    try:
        current_client_id = current_user.client
        user_plans = WorkoutPlan.objects.filter(client=current_client_id)
        user_sessions = WorkoutSession.objects.filter(completed_by=current_client_id)
    except Client.DoesNotExist as e:
        user_plans = []
        user_sessions = []
    return render(
        request, 'fitness/index.html',
        {'title': 'Client Portal', 'user': current_user, 'plans': user_plans, 'history': user_sessions}
    )


def all_workouts(request):
    current_client = request.user.client
    user_plans = WorkoutPlan.objects.filter(client=current_client)
    user_sessions = WorkoutSession.objects.filter(completed_by=current_client)
    return render(request, 'fitness/all_workouts.html',
                  {'title': 'All Workouts', 'user': request.user, 'plans': user_plans})


def recorded_workouts(request):
    current_client = request.user.client
    user_sessions = WorkoutSession.objects.filter(completed_by=current_client)
    return render(request, 'fitness/all_workouts.html',
                  {'title': 'All Workouts', 'user': request.user, 'history': user_sessions})


def workout(request, workout_slug):
    requested_workout = get_object_or_404(Workout, slug=workout_slug)

    if request.method == 'POST':
        SessionInputProcessor(
            workout=requested_workout,
            client=request.user.client,
            inputs=list(request.POST.items())
        ).process()

        return redirect('index')

    return render(request, 'fitness/workout.html',
                  {'title': requested_workout, 'workout': requested_workout})


def completed_session(request, session_id):
    requested_session = get_object_or_404(WorkoutSession, id=session_id)

    return render(request, 'fitness/completed_session.html',
                  {'title': requested_session.workout, 'session': requested_session})


def completed_chart(request):
    client = Client.objects.get(user=request.user)
    completed_sessions = (
        WorkoutSession.objects.filter(completed_by=client)
        .annotate(week_commencing=Trunc('completed_on', 'week', output_field=DateField()))
        .order_by('week_commencing')
    )

    sessions_by_week = {}
    for session in completed_sessions:
        sessions_by_week.setdefault(session.week_commencing, []).append(session)

    labels = [week.strftime('%b %e') for week in sessions_by_week]
    data = [len(sessions) for sessions in sessions_by_week.values()]

    return render(request, 'fitness/completed_sessions_chart.html',
                  {'labels': labels, 'data': data})


def monthly_calendar(request, year=datetime.datetime.today().year, month=datetime.datetime.today().month, user_id=None):
    if user_id:
        user = User.objects.get(pk=user_id)
    else:
        user = request.user

    year, month = int(year), int(month)
    month_calendar = calendar.monthcalendar(year, month)
    dtstart = datetime.datetime(year, month, 1)
    last_day_of_month = max(month_calendar[-1])

    workout_assignments = list(WorkoutAssignment.objects.filter(workout_plan__client__user=user))

    # Separate assignments assigned by weekday and assignments assigned by exact dates
    workout_assignments_by_weekday = {i: [] for i in range(7)}
    workout_assignments_by_date = {}

    for assignment in workout_assignments:
        # Group assignments by weekday
        for day in assignment.weekday:
            workout_assignments_by_weekday[int(day)].append(assignment)

        # Group assignments by exact dates
        for exact_date in assignment.exact_dates:
            if exact_date.month == month and exact_date.year == year:
                workout_assignments_by_date.setdefault(exact_date.day, []).append(assignment)

    # Build the month of workouts with a tuple per day - combining weekday and exact date assignments
    month_of_workouts = []
    for week_calendar in month_calendar:
        week_of_workouts = []
        for day_of_the_week, day_of_the_month in enumerate(week_calendar):
            if day_of_the_month == 0:
                week_of_workouts.append((0, []))  # Days not in this month
            else:
                workouts_for_day = set(workout_assignments_by_weekday[day_of_the_week])
                workouts_for_day.update(workout_assignments_by_date.get(day_of_the_month, []))
                week_of_workouts.append((day_of_the_month, list(workouts_for_day)))
        month_of_workouts.append(week_of_workouts)

    return render(request, 'fitness/calendar.html', {
        'title': 'Calendar',
        'weekdays': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'today': datetime.datetime.today(),
        'month_itinerary': month_of_workouts,
        'this_month': dtstart,
        'next_month': dtstart + datetime.timedelta(days=+last_day_of_month),
        'last_month': dtstart + datetime.timedelta(days=-1)
    })
