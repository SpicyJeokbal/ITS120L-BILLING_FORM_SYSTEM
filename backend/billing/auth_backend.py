# backend/billing/auth_backend.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .supabase_client import supabase_client
import hashlib

class SupabaseAuthBackend(BaseBackend):
    """
    Custom authentication backend that uses Supabase for user storage
    instead of Django's local database.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate user against Supabase"""
        if username is None or password is None:
            return None
        
        try:
            # Get user from Supabase
            user_data = supabase_client.get_user_by_username(username)
            
            if not user_data:
                return None
            
            # Verify password (stored as hash in Supabase)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if user_data.get('password_hash') != password_hash:
                return None
            
            # Create or update Django User object (in-memory, not saved to SQLite)
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': user_data.get('email', ''),
                    'first_name': user_data.get('full_name', ''),
                }
            )
            
            # Update user info if it changed
            if not created:
                user.email = user_data.get('email', '')
                user.first_name = user_data.get('full_name', '')
                user.save()
            
            return user
            
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None