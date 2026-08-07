from django.urls import path

from . import views

urlpatterns = [
    path('', views.assessment_list, name='assessment_list'),
    path('new/', views.assessment_create, name='assessment_create'),
    path('<int:pk>/', views.assessment_detail, name='assessment_detail'),
    path('<int:pk>/mark-failed/', views.assessment_mark_failed, name='assessment_mark_failed'),
    path('<int:pk>/delete/', views.assessment_delete, name='assessment_delete'),
]