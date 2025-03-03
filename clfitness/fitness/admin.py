from adminfilters.autocomplete import LinkedAutoCompleteFilter
from adminfilters.multiselect import UnionFieldListFilter
from django.contrib import admin

from adminsortable2.admin import SortableAdminBase, SortableInlineAdminMixin
from adminfilters.filters import AutoCompleteFilter
from adminfilters.mixin import AdminFiltersMixin
from django import forms
from django_jsonform.models.fields import JSONField
from django_jsonform.widgets import JSONFormWidget

from client_management.models import Client
from fitness.forms import WorkoutForm, StepsForm, WorkoutAssignmentForm
from fitness.models import Workout, ActivityCategory, Exercise, WorkoutPlan, WorkoutAssignment, ActivityThumbnail, \
    Set, WorkoutExercise, WorkoutSession, SessionExercise, Steps, CompletedSteps


class WorkoutExerciseInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Workout.exercises.through
    show_change_link = True


class SessionExerciseInline(admin.TabularInline):
    model = SessionExercise


class SetInline(SortableInlineAdminMixin, admin.TabularInline):
    model = Set


class WorkoutAssignmentInline(admin.TabularInline):
    model = WorkoutAssignment
    form = WorkoutAssignmentForm


@admin.register(ActivityThumbnail)
class ActivityThumbnailAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_file')
    search_fields = ('name', )


@admin.register(ActivityCategory)
class ActivityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )


@admin.register(Workout)
class WorkoutAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ('name', 'slug', 'difficulty', 'duration')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (WorkoutExerciseInline,)
    filter_horizontal = ('categories', )
    list_filter = ('categories', 'difficulty', 'exercises')
    search_fields = ('name',)

    form = WorkoutForm


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'difficulty')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('categories', 'difficulty')
    search_fields = ('name',)
    formfield_overrides = {JSONField: {"widget": JSONFormWidget(schema=Exercise.INSTRUCTIONS_SCHEMA)}}


@admin.register(WorkoutExercise)
class WorkoutExerciseAdmin(SortableAdminBase, admin.ModelAdmin):
    list_display = ('__str__',)
    inlines = (SetInline,)
    list_filter = ('workout', 'exercise')
    search_fields = ('workout__name', 'exercise__name')


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(AdminFiltersMixin, admin.ModelAdmin):
    list_display = ('__str__',)
    list_filter = (('workouts', AutoCompleteFilter), ('client', AutoCompleteFilter))
    inlines = (WorkoutAssignmentInline,)


@admin.register(WorkoutSession)
class WorkoutSessionAdmin(admin.ModelAdmin):
    list_display = ('workout', 'completed_by', 'completed_on')
    inlines = (SessionExerciseInline,)


@admin.register(SessionExercise)
class SessionExerciseAdmin(admin.ModelAdmin):
    pass


@admin.register(Steps)
class StepsAdmin(admin.ModelAdmin):
    form = StepsForm


@admin.register(CompletedSteps)
class StepsAdmin(admin.ModelAdmin):
    pass
