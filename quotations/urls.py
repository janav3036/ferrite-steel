from django.urls import path
from . import views

urlpatterns = [
    path('leads/', views.lead_list, name='lead_list'),
    path('leads/create/', views.lead_create, name='lead_create'),
    path('leads/<int:pk>/', views.lead_detail, name='lead_detail'),
    path('leads/<int:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('leads/<int:pk>/save-notes/', views.lead_save_notes, name='lead_save_notes'),
    path('', views.quotation_list, name='quotation_list'),
    path('select-lead/', views.quotation_select_lead, name='quotation_select_lead'),
    path('create/<int:lead_pk>/', views.quotation_create, name='quotation_create'),
    path('<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('<int:pk>/edit/', views.quotation_edit, name='quotation_edit'),
    path('<int:pk>/pdf/', views.quotation_pdf, name='quotation_pdf'),
    path('<int:pk>/pdf-edit/', views.quotation_pdf_edit, name='quotation_pdf_edit'),
    path('<int:pk>/outcome/', views.quotation_outcome, name='quotation_outcome'),
    path('<int:pk>/revise/', views.quotation_revise, name='quotation_revise'),
    path('<int:pk>/send/', views.quotation_send, name='quotation_send'),
    path('<int:pk>/approve/', views.quotation_approve, name='quotation_approve'),
    path('<int:pk>/delete/', views.quotation_delete, name='quotation_delete'),
    path('<int:pk>/notes/', views.quotation_save_notes, name='quotation_save_notes'),

    # Market Orders
    path('market-orders/', views.market_order_list, name='market_order_list'),
    path('market-orders/create/', views.market_order_create, name='market_order_create'),
    path('market-orders/<int:pk>/', views.market_order_detail, name='market_order_detail'),
    path('market-orders/<int:pk>/set-rate/', views.market_order_set_rate, name='market_order_set_rate'),
    path('market-orders/<int:pk>/confirm/', views.market_order_confirm, name='market_order_confirm'),
    path('market-orders/<int:pk>/assign-do/', views.market_order_assign_do, name='market_order_assign_do'),
    path('market-orders/<int:pk>/set-do/', views.market_order_set_do, name='market_order_set_do'),

    path('poll-now/', views.poll_emails_now, name='poll_emails_now'),
    path('market-orders/<int:pk>/do-send/', views.market_order_do_send, name='market_order_do_send'),

]
