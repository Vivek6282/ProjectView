from django.urls import path
from . import views
from projects import views as project_views
from chat import views as chat_views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('analytics.json/', views.analytics_json, name='analytics_json'),
    path('projects/', project_views.admin_project_list, name='admin_project_list'),
    path('projects/create/', project_views.admin_project_create, name='admin_project_create'),
    path('projects/<int:pk>/edit/', project_views.admin_project_edit, name='admin_project_edit'),
    path('projects/<int:pk>/delete/', project_views.admin_project_delete, name='admin_project_delete'),
    path('chat/', chat_views.admin_chat_hub, name='admin_chat'),
    path('chat/create/', chat_views.admin_create_room, name='admin_create_room'),
    path('chat/direct/<int:user_id>/', chat_views.direct_chat_view, name='admin_direct_chat'),
]
