# URL Reference — FERITE-STEEL

## aegis (prefix: `/`)

| URL | View / Name |
|----|-------------|
| `/login/` | LoginView |
| `/logout/` | LogoutView |
| `/dashboard/` | dashboard |
| `/register/` | register |
| `/add-user/` | add_user (admin only) |
| `/directory/` | user_directory (admin) |
| `/directory/<id>/edit-role/` | edit_user_role (admin) |
| `/approve-user/<id>/` | approve_user (admin) |
| `/delete-user/<id>/` | delete_user (admin) |
| `/password-reset/` | PasswordResetView |
| `/password-reset/done/` | PasswordResetDoneView |
| `/password-reset/confirm/<uid>/<token>/` | PasswordResetConfirmView |
| `/password-reset/complete/` | PasswordResetCompleteView |

## quotations (prefix: `/quotations/`)

| URL | View / Name |
|----|-------------|
| `/quotations/` | quotation_list |
| `/quotations/select-lead/` | quotation_select_lead |
| `/quotations/create/<lead_pk>/` | quotation_create |
| `/quotations/<pk>/` | quotation_detail |
| `/quotations/<pk>/edit/` | quotation_edit |
| `/quotations/<pk>/pdf/` | quotation_pdf |
| `/quotations/<pk>/approve/` | quotation_approve |
| `/quotations/<pk>/outcome/` | quotation_outcome |
| `/quotations/<pk>/revise/` | quotation_revise |
| `/quotations/<pk>/send/` | quotation_send |
| `/quotations/leads/` | lead_list |
| `/quotations/leads/create/` | lead_create |
| `/quotations/leads/<pk>/` | lead_detail |
| `/quotations/leads/<pk>/save-notes/` | lead_save_notes (POST only) |
| `/quotations/market-orders/` | market_order_list |
| `/quotations/market-orders/create/` | market_order_create |
| `/quotations/market-orders/<pk>/` | market_order_detail |
| `/quotations/market-orders/<pk>/set-rate/` | market_order_set_rate |
| `/quotations/market-orders/<pk>/confirm/` | market_order_confirm |
| `/quotations/market-orders/<pk>/assign-do/` | market_order_assign_do |
| `/quotations/market-orders/<pk>/set-do/` | market_order_set_do |

## database (prefix: `/database/`)

| URL | View / Name |
|----|-------------|
| `/database/products/` | product_list |
| `/database/products/add/` | product_add |
| `/database/products/catalog.json` | product_catalog_json |
| `/database/products/<pk>/edit/` | product_edit |
| `/database/products/<pk>/delete/` | product_delete |
| `/database/customers/` | customer_list |
| `/database/customers/add/` | customer_add |
| `/database/customers/<pk>/` | customer_detail |
| `/database/customers/<pk>/edit/` | customer_edit |
| `/database/brokers/` | broker_list |
| `/database/brokers/add/` | broker_create |

## training (prefix: `/training/`)

| URL | View / Name |
|----|-------------|
| `/training/` | training_home |
| `/training/cases/` | case_list |
| `/training/cases/create/` | case_create |
| `/training/cases/<pk>/` | case_detail |
| `/training/cases/<pk>/edit/` | case_edit |
| `/training/cases/<pk>/delete/` | case_delete |

**admin:** `/admin/` — jazzmin-themed Django admin.
