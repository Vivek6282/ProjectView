from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('intro/', views.intro_view, name='intro'),
    path('dashboard/users/', views.user_list_view, name='user_list'),
    path('dashboard/users/create/', views.user_create_view, name='user_create'),
    path('dashboard/users/<int:user_id>/toggle/', views.user_toggle_active, name='user_toggle'),
    path('dashboard/users/<int:user_id>/message/', views.send_message, name='send_message'),
    path('messages/<int:message_id>/acknowledge/', views.acknowledge_message, name='acknowledge_message'),
]
