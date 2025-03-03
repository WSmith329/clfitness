from django.forms import ModelForm, DateField, forms, widgets, BooleanField
from django.utils import timezone

from client_management.models import MeasurementRecording


class MeasurementRecordingForm(ModelForm):
    class Meta:
        model = MeasurementRecording
        fields = ['weight', 'height', 'body_fat', 'bmi']

    def save(self, commit=True, user=None):
        measurement_recording = super(MeasurementRecordingForm, self).save(commit=False)

        measurement_recording.recorded = timezone.now()

        if user and hasattr(user, 'client'):
            measurement_recording.client = user.client

        if commit:
            measurement_recording.save()
        return measurement_recording


class CompletedDateForm(forms.Form):
    completed_date = DateField(
        required=False,
        widget=widgets.DateInput(attrs={'type': 'date'}),
        help_text='Leave blank to automatically set to today.'
    )
    ignore_unpaid = BooleanField(
        required=False,
        help_text='This only applies if the amount paid does not match the amount due.'
    )
