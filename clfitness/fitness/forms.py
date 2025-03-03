from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.forms import MultiWidget, DateInput
from django.forms.utils import ErrorList
from django_jsonform.widgets import JSONFormWidget
from durationwidget.widgets import TimeDurationWidget

from .models import Workout, WorkoutSession, Steps, Weekday, WorkoutAssignment, CompletedSteps


class MultiDateInputWidget(MultiWidget):
    def __init__(self, attrs=None):
        widgets = [DateInput(attrs={'type': 'date', 'class': 'date-input'})]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if value:
            return value
        return [None]


class WorkoutForm(forms.ModelForm):
    duration = forms.DurationField(widget=TimeDurationWidget(
        show_days=False, show_hours=True, show_minutes=True, show_seconds=False
    ), required=False)

    class Meta:
        model = Workout
        fields = '__all__'


class WorkoutAssignmentForm(forms.ModelForm):
    weekday = forms.MultipleChoiceField(
        choices=Weekday.choices,
        widget=forms.CheckboxSelectMultiple
    )

    def clean_weekday(self):
        data = self.cleaned_data['weekday']
        return [int(day) for day in data]

    class Meta:
        model = WorkoutAssignment
        fields = '__all__'


class WorkoutSessionForm(forms.ModelForm):
    class Meta:
        model = WorkoutSession
        fields = ['completed_by']


class StepsForm(forms.ModelForm):
    weekday = forms.MultipleChoiceField(
        choices=Weekday.choices,
        widget=forms.CheckboxSelectMultiple
    )

    def clean_weekday(self):
        data = self.cleaned_data['weekday']
        return [int(day) for day in data]

    class Meta:
        model = Steps
        fields = '__all__'


class CompletedStepsForm(forms.ModelForm):
    class Meta:
        model = CompletedSteps
        fields = ['completed']
