import pytest

from django.test import RequestFactory
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.contrib import admin

from client_management.admin import ClientStatusFilter, UserAdmin
from client_management.models import Client


@pytest.fixture
def client_status_filter():
    return ClientStatusFilter(
        model=User,
        model_admin=admin.ModelAdmin(User, admin.site),
        params={},
        request=RequestFactory().get('/')
    )


def test_clientstatusfilter_lookups(client_status_filter):
    lookups = client_status_filter.lookups(None, None)

    assert lookups == (
        ('is_client', _('Yes')),
        ('not_client', _('No'))
    )


@pytest.mark.parametrize(
    'client_status, populate_client, expected_queryset, expected_count', [
        pytest.param(
            'is_client',
            True,
            User.objects.filter(client__isnull=False),
            1,
            id='is-client-with-client'
        ),
        pytest.param(
            'is_client',
            False,
            User.objects.filter(client__isnull=False),
            0,
            id='is-client-without-client'
        ),
        pytest.param(
            'not_client',
            True,
            User.objects.filter(client__isnull=True),
            0,
            id='not-client-with-client'
        ),
        pytest.param(
            'not_client',
            False,
            User.objects.filter(client__isnull=True),
            1,
            id='not-client-without-client'
        )
    ]
)
def test_clientstatusfilter_queryset(client_status, populate_client, expected_queryset, expected_count,
                                     client_status_filter, db, monkeypatch):
    model = User

    # sanity checks
    queryset = client_status_filter.queryset(request=None, queryset=User.objects.all())
    assert list(queryset) == []

    user = model.objects.create(
        username='TestUser',
        password='password'
    )

    # make user a client if flagged
    if populate_client:
        Client.objects.create(
            user=user
        )

    def mock_value(self):
        return client_status
    monkeypatch.setattr(
        'django.contrib.admin.filters.SimpleListFilter.value',
        mock_value
    )

    queryset = client_status_filter.queryset(request=None, queryset=model.objects.all())
    assert list(queryset) == list(expected_queryset)
    assert len(list(queryset)) == expected_count


@pytest.mark.parametrize(
    'populate_client, expected_status', [
        pytest.param(
            False,
            False,
            id='is-client'
        ),
        pytest.param(
            True,
            True,
            id='not-client'
        )
    ]
)
def test_useradmin_client_status(populate_client, expected_status, db):
    user = User.objects.create(
        username='TestUser',
        password='password'
    )

    if populate_client:
        Client.objects.create(
            user=user
        )

    user_admin = UserAdmin(model=User, admin_site=admin.site)

    returned_status = user_admin.client_status(obj=user)

    assert returned_status == expected_status
