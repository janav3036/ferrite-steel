from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('send/', views.chat_send, name='chat_send'),
    path('poll/', views.chat_poll, name='chat_poll'),
    path('search/', views.chat_search, name='chat_search'),
    path('channels.json', views.chat_channels_json, name='chat_channels_json'),
    path('read-status/', views.chat_read_status, name='chat_read_status'),
]
