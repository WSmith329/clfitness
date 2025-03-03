"""
URL configuration for clfitness project.
"""
from django.contrib import admin
from django.contrib.admin.sites import site
from django.contrib.auth.decorators import login_required
from django.urls import include, path, re_path
from django.conf import settings
from django.conf.urls.static import static
import adminactions.actions as actions

from clfitness import views

site.site_title = 'Chloe Leanne Fitness'
site.site_header = 'Chloe Leanne Fitness'
site.enable_nav_sidebar = True

actions.add_to_site(site)

urlpatterns = (([
    path('admin/', admin.site.urls),
    path('accounts/', login_required(views.account), name='account'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('client_management.urls')),
    path('', login_required(views.dashboard), name='dashboard'),
    path('fitness/', include('fitness.urls')),
    re_path(r'^adminactions/', include('adminactions.urls'))
]
               + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
               + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))
