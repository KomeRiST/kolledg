from django.conf.urls import url
from login_auth import views as login_views
from django.conf import settings


urlpatterns = [
    url(r'^login/$', login_views.login, name='login'),
    url(r'^logout/$', login_views.logout, name='logout'),
]