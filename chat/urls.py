from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('send/', views.chat_send, name='chat_send'),
    path('poll/', views.chat_poll, name='chat_poll'),
]
