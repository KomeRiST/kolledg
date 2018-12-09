from django.contrib import admin
from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^$', views.index, name='index'),
    url(r'^group/(?P<group_id>[0-9]+)/$', views.group, name='group'),
    url(r'^stud/(?P<stud_id>[0-9]+)/$', views.get_stud, name='get_stud'),
    url(r'^prikaz/(?P<tip>[A-z]+)/$', views.prikaz, name='prikaz'),
    url(r'^prik/(?P<tip>[A-z]+)/(?P<prik_id>[0-9]+)/$', views.prik, name='prik'),
    url(r'^prikaz_new/', views.new_prikaz, name='new_prikaz'),
    url(r'^prikaz_new_perevod/', views.prikaz_new_perevod, name='prikaz_new_perevod'),
    url(r'^export/uch_plan/(?P<group_id>[0-9]+)/$', views.excel, name='excel'),
    url(r'^import/uch_plan/(?P<group_id>[0-9]+)/$', views.import_excel, name='import_excel'),
    url(r'^prikaz_povtornaya/', views.prikaz_povtornaya, name='prikaz_povtornaya'),
    url(r'^print/(?P<tip>[A-z]+)/$', views.print_, name='print'),
    url(r'^prikazy/', views.prikazy, name='prikazy'),
    url(r'^save_up/', views.save_up, name='save_up'),
    url(r'^begunok_get/(?P<beg_id>[0-9]+)/$', views.begunok_print, name='begunok_print'),
    url(r'^begunok_set/(?P<beg_id>[0-9]+)/$', views.begunok_set, name='begunok_set'),
    url(r'^vedomosty/(?P<disc_id>[0-9]+)/$', views.vedomost_get, name='vedomost_get'),
    url(r'^new_vedomost/(?P<disc_id>[0-9]+)/$', views.new_vedomost, name='new_vedomost'),
    url(r'^studs_ved/(?P<tip>[A-z]+)/(?P<ved_id>[0-9]+)/$', views.studs_ved, name='studs_ved'),
    url(r'^prepod_info/(?P<prepod_id>[0-9]+)/$', views.prepod_info, name='prepod_info'),
]