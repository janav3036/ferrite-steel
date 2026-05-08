from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from django.views.generic import RedirectView
from .views import dashboard, add_user, user_directory, edit_user_role, register, approve_user, delete_user

urlpatterns = [
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('add-user/', add_user, name='add_user'),
    path('directory/', user_directory, name='user_directory'),
    path('directory/<int:user_id>/edit-role/', edit_user_role, name='edit_user_role'),
    path('register/', register, name='register'),
    path('approve-user/<int:user_id>/', approve_user, name='approve_user'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]