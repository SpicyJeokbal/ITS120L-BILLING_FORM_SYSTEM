# backend/billing/user_management_views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from .supabase_client import supabase_client
from .decorators import head_librarian_required
import json
import hashlib

@head_librarian_required
def user_management_page(request):
    """User management page - Head Librarian only"""
    # Get all users
    users = supabase_client.get_all_users()
    
    context = {
        'users': users,
        'current_user': request.user.username
    }
    return render(request, 'user_management.html', context)

@csrf_exempt
@require_POST
@head_librarian_required
def create_user_admin(request):
    """Create new user account - Head Librarian only"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['username', 'email', 'full_name', 'password', 'role']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f"Missing fields: {', '.join(missing_fields)}"
            }, status=400)
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        # Check if user already exists
        if supabase_client.get_user_by_username(username):
            return JsonResponse({
                'success': False,
                'message': 'Username already exists'
            }, status=400)
        
        if supabase_client.get_user_by_email(email):
            return JsonResponse({
                'success': False,
                'message': 'Email already registered'
            }, status=400)
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Create user in Supabase
        user_data = {
            'username': username,
            'email': email,
            'full_name': data.get('full_name'),
            'password_hash': password_hash,
            'role': data.get('role', 'librarian'),
            'status': 'active',
            'can_access': True
        }
        
        new_user = supabase_client.create_user_by_admin(user_data)
        
        if new_user:
            # Log the activity
            log_details = f"Created new user: {username} ({data.get('full_name')}) with role: {data.get('role')}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='create_user',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'User created successfully',
                'user': new_user
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to create user'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@head_librarian_required
def update_user_status_view(request):
    """Update user status (suspend/activate) - Head Librarian only"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        status = data.get('status')
        
        if not username or not status:
            return JsonResponse({
                'success': False,
                'message': 'Username and status required'
            }, status=400)
        
        # Prevent self-suspension
        if username == request.user.username:
            return JsonResponse({
                'success': False,
                'message': 'Cannot change your own status'
            }, status=400)
        
        success = supabase_client.update_user_status(username, status)
        
        if success:
            # Log the activity
            log_details = f"Changed {username}'s status to: {status}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='update_user_status',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': f'User status updated to {status}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update status'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@head_librarian_required
def update_user_role_view(request):
    """Update user role - Head Librarian only"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        role = data.get('role')
        
        if not username or not role:
            return JsonResponse({
                'success': False,
                'message': 'Username and role required'
            }, status=400)
        
        # Prevent changing own role
        if username == request.user.username:
            return JsonResponse({
                'success': False,
                'message': 'Cannot change your own role'
            }, status=400)
        
        success = supabase_client.update_user_role(username, role)
        
        if success:
            # Log the activity
            log_details = f"Changed {username}'s role to: {role}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='update_user_role',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': f'User role updated to {role}'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update role'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@head_librarian_required
def reset_password_view(request):
    """Reset user password - Head Librarian only"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        new_password = data.get('new_password')
        
        if not username or not new_password:
            return JsonResponse({
                'success': False,
                'message': 'Username and new password required'
            }, status=400)
        
        # Hash new password
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        success = supabase_client.reset_user_password(username, password_hash)
        
        if success:
            # Log the activity
            log_details = f"Reset password for user: {username}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='reset_password',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Password reset successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to reset password'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@head_librarian_required
def delete_user_view(request):
    """Delete user account - Head Librarian only"""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        
        if not username:
            return JsonResponse({
                'success': False,
                'message': 'Username required'
            }, status=400)
        
        # Prevent self-deletion
        if username == request.user.username:
            return JsonResponse({
                'success': False,
                'message': 'Cannot delete your own account'
            }, status=400)
        
        success = supabase_client.delete_user(username)
        
        if success:
            # Log the activity
            log_details = f"Deleted user account: {username}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='delete_user',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'User deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to delete user'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)