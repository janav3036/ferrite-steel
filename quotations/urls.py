from django.urls import path
from . import views

urlpatterns = [
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/create/', views.lead_create, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('', views.quotation_list, name='quotation_list'),
    path('<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('<int:pk>/approve/', views.quotation_approve, name='quotation_approve'),
]
