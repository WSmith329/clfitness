import datetime

from django.db.models import Q
from django.shortcuts import render, redirect

from fitness.forms import CompletedStepsForm
from fitness.models import WorkoutAssignment, Weekday, Steps, CompletedSteps


def account(request):
    current_user = request.user
    return render(request, 'registration/account.html',
                  {'title': 'Your Account', 'user': current_user})


def dashboard(request):
    current_user = request.user

    title = f'{current_user.first_name} {current_user.last_name}' if current_user.first_name and current_user.last_name\
        else current_user.username

    today = datetime.date.today()

    if not hasattr(current_user, 'client'):
        return render(
            request,
            'core/dashboard.html',
            {
                'title': title, 'user': current_user
            }
        )

    workout_assignments_today = WorkoutAssignment.objects.filter(
        Q(weekday__contains=[today.weekday()]) |
        Q(exact_dates__contains=[today]),
        workout_plan__client=current_user.client
    )

    try:
        steps_today = Steps.objects.get(
            weekday__contains=[today.weekday()], client=current_user.client
        )
    except Steps.DoesNotExist:
        steps_today = None

    try:
        completed_steps_today = CompletedSteps.objects.get(
            completed_on=today, completed_by=current_user.client
        )
        steps_progress = min(100, int((completed_steps_today.completed/completed_steps_today.aim)*100))
    except CompletedSteps.DoesNotExist:
        completed_steps_today = None
        steps_progress = 0

    if request.method == 'POST':
        form = CompletedStepsForm(request.POST, instance=completed_steps_today)
        if form.is_valid():
            completed_steps = form.save(commit=False)
            completed_steps.aim = steps_today.amount
            completed_steps.completed_by = current_user.client
            completed_steps.save()
            return redirect('dashboard')
    else:
        form = CompletedStepsForm(instance=completed_steps_today)

    return render(
        request,
        'core/dashboard.html',
        {
            'title': title, 'user': current_user,
            'workout_assignments_today': workout_assignments_today,
            'steps_today': steps_today,
            'steps_progress': steps_progress,
            'steps_form': form
        }
    )
