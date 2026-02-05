# backend/billing/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('update-status/', views.update_status, name='update_status'),
    path('create-item/', views.create_item, name='create_item'),
]