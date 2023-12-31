from django.urls import path

from . import views

app_name= 'GenomelEditor'

urlpatterns = [
    path('', views.index, name='index'),
    path('logout', views.logout_user, name='logout'),
    path('login', views.login_user, name='login'),
    path('annotate', views.annotate, name='annotate'),
    path('save_annotation', views.save_annotation, name='save_annotation'),
    path('admin_dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('help', views.help, name='help'),
    path('upload_chants', views.upload_chants, name='upload_chants'),
    path('upload_sources', views.upload_sources, name='upload_sources'),
]
