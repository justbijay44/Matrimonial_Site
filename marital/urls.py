
from django.urls import path
from django.contrib.auth.views import LoginView
from . import views

app_name = 'marital'

urlpatterns = [
    path('', views.home, name='home'),
    path('editprofile/', views.edit_profile, name='edit_profile'),
    path('matches/', views.matches, name='matches'),
    path('match/<int:match_id>/action/', views.match_action, name='match_action'),
    path('messages/<int:match_id>/', views.match_messages, name='messages'),
    path('register/', views.register, name='register'),
    path('login/',LoginView.as_view(template_name='marital/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
]