# backend/billing/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .supabase_client import supabase_client

def head_librarian_required(view_func):
    """Decorator to restrict access to head librarian only"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        
        # Get user profile from Supabase
        user_profile = supabase_client.get_user_by_username(request.user.username)
        
        if not user_profile:
            messages.error(request, 'User profile not found.')
            return redirect('dashboard')
        
        # Check if user is head librarian
        if user_profile.get('role') != 'head_librarian':
            messages.error(request, 'Access denied. Head Librarian privileges required.')
            return redirect('dashboard')
        
        # Check if account is active
        if not user_profile.get('can_access'):
            messages.error(request, 'Your account has been suspended.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view

def active_user_required(view_func):
    """Decorator to check if user account is active"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Get user profile from Supabase
        user_profile = supabase_client.get_user_by_username(request.user.username)
        
        if not user_profile:
            messages.error(request, 'User profile not found.')
            return redirect('login')
        
        # Check if account is active
        if not user_profile.get('can_access') or user_profile.get('status') != 'active':
            messages.error(request, 'Your account has been suspended. Please contact the head librarian.')
            return redirect('login')
        
        return view_func(request, *args, **kwargs)
    
    return wrapped_view