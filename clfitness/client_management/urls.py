from django.urls import path
from django.contrib.auth.decorators import login_required

from .views import measurement_recording

urlpatterns = [
    path('measurement-recording/', login_required(measurement_recording), name='measurement_recording')
]
