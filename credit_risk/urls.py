from django.urls import path

from . import views

urlpatterns = [
    path('', views.assessment_list, name='assessment_list'),
    path('new/', views.assessment_create, name='assessment_create'),
    path('<int:pk>/', views.assessment_detail, name='assessment_detail'),
]