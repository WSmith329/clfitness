import sentry_sdk
from django.http import HttpResponseServerError
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from .forms import MeasurementRecordingForm


@require_http_methods(['GET', 'POST'])
def measurement_recording(request):
    if request.method == 'POST':
        form = MeasurementRecordingForm(request.POST)
        if form.is_valid():
            form.save(user=request.user)
            return redirect('account')

    else:
        form = MeasurementRecordingForm()

    return render(request, 'client_management/measurement_recording.html',
                  {'title': 'Enter new recording', 'form': form})
