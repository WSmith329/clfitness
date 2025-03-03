import datetime
from pathlib import Path

from django.contrib.postgres.fields import ArrayField
from django_jsonform.models.fields import ArrayField as JSONFormArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from django_jsonform.models.fields import JSONField


class AbstractActivity(models.Model):
    class LevelsOfDifficulty(models.TextChoices):
        UNASSIGNED = 'UN', _('Unassigned')
        BASIC = 'BA', _('Basic')
        MODERATE = 'MO', _('Moderate')
        INTERMEDIATE = 'IN', _('Intermediate')
        ADVANCED = 'AD', _('Advanced')

    name = models.CharField(unique=True, max_length=50)
    slug = models.SlugField(unique=True, max_length=50)
    description = models.TextField(blank=True)
    categories = models.ManyToManyField('ActivityCategory', blank=True)
    difficulty = models.CharField(
        choices=LevelsOfDifficulty,
        default=LevelsOfDifficulty.UNASSIGNED,
        max_length=2
    )
    thumbnail = models.ForeignKey('ActivityThumbnail', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        abstract = True
        managed = False

    def __str__(self):
        return self.name


class ActivityThumbnail(models.Model):
    name = models.CharField(max_length=100, editable=False, blank=True)
    image_file = models.ImageField(upload_to='thumbnails/', width_field='width', height_field='height')
    width = models.PositiveSmallIntegerField(editable=False, default=1280)
    height = models.PositiveSmallIntegerField(editable=False, default=720)

    class Meta:
        verbose_name = 'Thumbnail'
        verbose_name_plural = 'Thumbnails'

    def save(self, *args, **kwargs):
        path = Path(str(self.image_file))
        extensions = "".join(path.suffixes)
        self.name = str(path).removesuffix(extensions)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ActivityCategory(models.Model):
    name = models.CharField(unique=True, max_length=30)

    class Meta:
        verbose_name_plural = 'Categories'
        verbose_name = 'Category'
        ordering = ['name']

    def __str__(self):
        return self.name


class Exercise(AbstractActivity):
    INSTRUCTIONS_SCHEMA = {
        'type': 'array',
        'title': 'Instructions',
        'description': 'Add instructions for the exercise',
        'items': {
            'type': 'string',
            'widget': 'textarea'
        },
        'minItems': 0,
        'maxItems': 10
    }
    instructions = JSONField(schema=INSTRUCTIONS_SCHEMA)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        ordering = ['name']


class Workout(AbstractActivity):
    exercises = models.ManyToManyField(
        'Exercise',
        through='WorkoutExercise'
    )
    duration = models.DurationField(null=True, blank=True)

    class Meta:
        managed = True
        ordering = ['name']


class WorkoutExercise(models.Model):
    exercise = models.ForeignKey('Exercise', on_delete=models.CASCADE)
    workout = models.ForeignKey('Workout', on_delete=models.CASCADE)

    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.workout.name} ({self.exercise.name})'

    class Meta:
        ordering = ['order']


class Set(models.Model):
    workout_exercise = models.ForeignKey('WorkoutExercise', on_delete=models.CASCADE)

    order = models.PositiveIntegerField(default=0)

    time = models.DurationField(null=True, blank=True)
    reps = models.PositiveIntegerField(null=True, blank=True)
    until_failure = models.BooleanField(default=False, verbose_name='until failure')

    class WeightLevels(models.TextChoices):
        UNSPECIFIED = 'UN', _('Unspecified')
        LIGHT = 'LI', _('Light')
        MODERATE = 'MO', _('Moderate')
        HEAVY = 'HE', _('Heavy')
        MAXIMUM = 'MA', _('Maximum')

    weight_level = models.CharField(max_length=2, choices=WeightLevels.choices, default=WeightLevels.UNSPECIFIED)

    class Meta:
        ordering = ['order']

    def clean(self):
        if self.until_failure and (self.time or self.reps):
            raise ValidationError(
                _('until_failure cannot be selected whilst having reps/time set.')
            )
        elif self.time and self.reps:
            raise ValidationError(
                _('time and reps cannot both be set.')
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class WorkoutPlan(models.Model):
    workouts = models.ManyToManyField(
        'Workout',
        through='WorkoutAssignment'
    )
    client = models.ForeignKey('client_management.Client', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.client} ({self.id})'


class Weekday(models.IntegerChoices):
    MONDAY = 0, _('Monday')
    TUESDAY = 1, _('Tuesday')
    WEDNESDAY = 2, _('Wednesday')
    THURSDAY = 3, _('Thursday')
    FRIDAY = 4, _('Friday')
    SATURDAY = 5, _('Saturday')
    SUNDAY = 6, _('Sunday')


EXACT_DATES_SCHEMA = {
    "type": "array",
    "title": "Exact Dates",
    "items": {
        "type": "string",
        "format": "date"
    }}


class WorkoutAssignment(models.Model):
    workout = models.ForeignKey('Workout', on_delete=models.CASCADE)
    workout_plan = models.ForeignKey('WorkoutPlan', on_delete=models.CASCADE)

    weekday = ArrayField(
        models.IntegerField(choices=Weekday.choices, blank=True),
        default=list
    )

    exact_dates = JSONFormArrayField(
        models.DateField(),
        schema=EXACT_DATES_SCHEMA,
        default=list,
        blank=True
    )

    def __str__(self):
        return f'{self.workout_plan} - {self.workout.name}'


class WorkoutSession(models.Model):
    workout = models.ForeignKey('Workout', on_delete=models.RESTRICT)
    completed_by = models.ForeignKey('client_management.Client', on_delete=models.CASCADE)
    completed_on = models.DateTimeField(auto_now_add=True, blank=True)
    completed_exercises = models.ManyToManyField(
        'WorkoutExercise',
        through='SessionExercise'
    )

    def __str__(self):
        return f'{ self.completed_by } ({ self.completed_on })'


class SessionExercise(models.Model):
    session = models.ForeignKey('WorkoutSession', on_delete=models.CASCADE)
    workout_exercise = models.ForeignKey('WorkoutExercise', on_delete=models.RESTRICT)

    SET_RECORDINGS_SCHEMA = {
        "type": "array",
        "title": "Set Records",
        "description": "Record the reps achieved during each set",
        "items": {
            "type": "object",
            "keys": {
                "order": {
                    "type": "integer"
                },
                "aim": {
                    "type": "integer"
                },
                "completed": {
                    "type": "integer"
                },
                "weight": {
                    "type": "integer"
                }
            }
        }
    }
    set_recordings = JSONField(schema=SET_RECORDINGS_SCHEMA)

    def __str__(self):
        return f'{ self.session } ({ self.workout_exercise.exercise.name })'


class Steps(models.Model):
    amount = models.PositiveIntegerField()
    weekday = ArrayField(
        models.IntegerField(choices=Weekday.choices, blank=True),
        default=list
    )
    client = models.ForeignKey('client_management.Client', on_delete=models.CASCADE)


class CompletedSteps(models.Model):
    aim = models.PositiveIntegerField()
    completed = models.PositiveIntegerField()
    completed_by = models.ForeignKey('client_management.Client', on_delete=models.CASCADE)
    completed_on = models.DateField(auto_now_add=True)
