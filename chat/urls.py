from django.urls import path
from . import views

urlpatterns = [
    # Employee views
    path('', views.employee_chat_hub, name='employee_chat'),
    path('create/', views.employee_create_room, name='employee_create_room'),

    # API V2
    path('api/rooms/', views.api_rooms_list, name='api_rooms'),
    path('api/unread/counts/', views.api_unread_counts, name='api_unread_counts'),
    path('api/typing/', views.api_typing, name='api_typing'),
    path('api/user/<int:user_id>/direct-room/', views.api_direct_room, name='api_direct_room'),
    
    path('api/<int:room_id>/messages/', views.api_room_messages, name='api_room_messages'),
    path('api/<int:room_id>/send/', views.api_message_send, name='api_send'),
    path('api/<int:room_id>/read/', views.api_mark_read, name='api_mark_read'),
    path('api/<int:room_id>/delete/', views.api_delete_room, name='api_delete_room'),
    
    path('api/messages/<int:message_id>/edit/', views.api_message_edit, name='api_message_edit'),
    path('api/messages/<int:message_id>/delete/', views.api_message_delete, name='api_message_delete'),
    path('api/messages/<int:message_id>/forward/', views.api_message_forward, name='api_message_forward'),
]
