from django.urls import path

from . import views

app_name= 'GenomelEditor'

urlpatterns = [
    path('', views.index, name='index'),
    path('logout', views.logout_user, name='logout'),
    path('login', views.login_user, name='login'),
    path('upload_chants', views.upload_chants, name='upload_chants'),
    path('upload_sources', views.upload_sources, name='upload_sources'),
]