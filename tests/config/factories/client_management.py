import datetime

from factory import django, fuzzy

from client_management.models import Client, Payment


class PaymentFactory(django.DjangoModelFactory):
    class Meta:
        model = Payment

    due_date = fuzzy.FuzzyDate(datetime.date.today())
