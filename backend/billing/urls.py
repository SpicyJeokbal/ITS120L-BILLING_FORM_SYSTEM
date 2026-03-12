# backend/billing/urls.py
from django.urls import path
from . import views
from . import user_management_views

urlpatterns = [
    # =================== AUTHENTICATION ===================
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # =================== MAIN PAGES ===================
    path('', views.dashboard, name='dashboard'),
    path('students/', views.students_page, name='students_page'),
    path('fees/', views.fees_page, name='fees_page'),
    path('logs/', views.logs_page, name='logs_page'),
    path('archive/', views.archive_page, name='archive_page'),
    
    # =================== BILLING OPERATIONS ===================
    path('create-billing/', views.create_billing, name='create_billing'),
    path('get-billing/<int:item_id>/', views.get_billing, name='get_billing'),
    path('update-status/', views.update_status, name='update_status'),
    path('create-item/', views.create_item, name='create_item'),
    path('delete-billing/<int:item_id>/', views.delete_billing, name='delete_billing'),
    
    # =================== LOGS API ===================
    path('logs/api/', views.logs_api, name='logs_api'),
    
    # =================== STUDENT MANAGEMENT ===================
    path('students/upload/', views.upload_students, name='upload_students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/get/', views.get_student, name='get_student'),
    
    # =================== FEE MANAGEMENT ===================
    path('fees/', views.fees_page, name='fees_page'),
    path('fees/add/', views.add_fee, name='add_fee'),
    path('fees/update/', views.update_fee, name='update_fee'),
    path('fees/delete/', views.delete_fee, name='delete_fee'),
    path('fees/list/', views.list_fees_api, name='list_fees_api'),
    
    # =================== USER MANAGEMENT (HEAD LIBRARIAN ONLY) ===================
    path('user-management/', user_management_views.user_management_page, name='user_management'),
    path('user-management/create/', user_management_views.create_user_admin, name='create_user_admin'),
    path('user-management/update-status/', user_management_views.update_user_status_view, name='update_user_status'),
    path('user-management/update-role/', user_management_views.update_user_role_view, name='update_user_role'),
    path('user-management/reset-password/', user_management_views.reset_password_view, name='reset_password'),
    path('user-management/delete/', user_management_views.delete_user_view, name='delete_user'),

    # =================== STUDENT MANAGEMENT ===================
    path('students/', views.students_page, name='students_page'),
    path('students/upload/', views.upload_students, name='upload_students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/get/', views.get_student, name='get_student'),
    path('students/delete/', views.delete_student, name='delete_student'),
    path('students/list/', views.list_students_api, name='list_students_api'),

    # =================== SIGNATURE SETTINGS ===================
    path('signature-settings/', views.signature_settings_page, name='signature_settings'),
    path('signature-settings/save/', views.save_librarian_signature, name='save_librarian_signature'),
    path('signature-settings/get/', views.get_librarian_signature, name='get_librarian_signature'),

     # =================== ARCHIVE OPERATIONS ===================
    path('archive/', views.archive_page, name='archive_page'),
    path('archive/form/', views.archive_form, name='archive_form'),
    path('archive/restore/', views.restore_from_archive, name='restore_from_archive'),
    path('archive/delete/', views.delete_archived_form, name='delete_archived_form'),
    path('archive/auto-run/', views.run_auto_archive, name='run_auto_archive'),

    # =================== EXPORT/REPORTS ===================
    path('export/excel/', views.export_to_excel, name='export_excel'),
    path('export/pdf/', views.export_to_pdf, name='export_pdf'),

]