from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_view, name='project_list'),
    path('<int:pk>/', views.project_detail_view, name='project_detail'),
    path('<int:pk>/submit-complete/', views.submit_project_complete, name='project_submit_complete'),
]
