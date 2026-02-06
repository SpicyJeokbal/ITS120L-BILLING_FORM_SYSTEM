# backend/billing/urls.py
from django.urls import path
from . import views

urlpatterns = [

    #auth
    path('', views.login_page, name='login'),
    #path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_view, name='logout'),

    #main pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('students/', views.students_page, name='students'),
    path('fees/', views.fees_page, name='fees'),
    path('logs/', views.logs_page, name='logs'),
    path('archive/', views.archive_page, name='archive'),

    #auth
    path('update-status/', views.update_status, name='update_status'),
    path('create-item/', views.create_item, name='create_item'),
    path('create-billing/', views.create_billing, name='create_billing'),
    path('get-billing/<int:item_id>/', views.get_billing, name='get_billing'),
    path('upload-students/', views.upload_students, name='upload_students'),
    path('add-student/', views.add_student, name='add_student'),
    path('get-student/', views.get_student, name='get_student'),
    path('add-fee/', views.add_fee, name='add_fee'),
    path('delete-fee/', views.delete_fee, name='delete_fee'),
]