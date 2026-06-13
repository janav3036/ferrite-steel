from django.urls import path
from . import views

urlpatterns = [
    path('', views.guide_home, name='guide_home'),
    path('core/', views.guide_core, name='guide_core'),
    path('quotations/', views.guide_quotations, name='guide_quotations'),
    path('training/', views.guide_training, name='guide_training'),
]
