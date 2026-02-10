# backend/billing/context_processors.py
from .supabase_client import supabase_client

def user_role(request):
    """Add user role to template context"""
    if request.user.is_authenticated:
        user_profile = supabase_client.get_user_by_username(request.user.username)
        if user_profile:
            return {
                'user_role': user_profile.get('role', 'librarian'),
                'is_head_librarian': user_profile.get('role') == 'head_librarian',
                'user_status': user_profile.get('status', 'active'),
                'can_access': user_profile.get('can_access', True)
            }
    return {
        'user_role': None,
        'is_head_librarian': False,
        'user_status': None,
        'can_access': False
    }