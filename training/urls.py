from django.urls import path
from . import views

urlpatterns = [
    path('', views.training_home, name='training_home'),
    path('cases/', views.case_list, name='case_list'),
    path('cases/create/', views.case_create, name='case_create'),
    path('cases/<int:pk>/', views.case_detail, name='case_detail'),
    path('cases/<int:pk>/edit/', views.case_edit, name='case_edit'),
    path('cases/<int:pk>/delete/', views.case_delete, name='case_delete'),
]
