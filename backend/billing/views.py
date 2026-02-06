# backend/billing/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .supabase_client import supabase_client
import json
import re

def login_page(request):

    """Login page view with security"""
    print("\n=== LOGIN PAGE DEBUG ===")
    print(f"Request method: {request.method}")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"Session key: {request.session.session_key}")

    """Login page view with security"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # Basic input validation
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'login.html')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Log the user activity in Supabase
            supabase_client.log_user_activity(user.username, 'login')
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')
    
    return render(request, 'login.html')

def register_page(request):

    print("=== REGISTER VIEW CALLED ===")
    print(f"Method: {request.method}")

    """Registration page view with security"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        # Validation
        errors = []
        
        # Check all fields are filled
        if not all([full_name, email, username, password, confirm_password]):
            errors.append('All fields are required.')
        
        # Validate Mapua email
        if not email.endswith('@mymail.mapua.edu.ph'):
            errors.append('Please use a valid Mapua email address.')
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            errors.append('Invalid email format.')
        
        # Username validation (alphanumeric, 4-20 chars)
        if not re.match(r'^[a-zA-Z0-9_]{4,20}$', username):
            errors.append('Username must be 4-20 characters (letters, numbers, underscore only).')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            errors.append('Username already taken.')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            errors.append('Email already registered.')
        
        # Password validation
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        # Check password strength
        if not any(c.isupper() for c in password):
            errors.append('Password must contain at least one uppercase letter.')
        
        if not any(c.isdigit() for c in password):
            errors.append('Password must contain at least one number.')
        
        # If there are errors, show them
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'register.html')
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name
            )
            
            # Store user info in Supabase
            supabase_client.create_user_profile({
                'username': username,
                'email': email,
                'full_name': full_name,
                'created_at': user.date_joined.isoformat()
            })
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')

def logout_view(request):
    """Logout view with activity logging"""
    username = request.user.username if request.user.is_authenticated else 'unknown'
    
    # Log logout activity
    supabase_client.log_user_activity(username, 'logout')
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required(login_url='login')
def dashboard(request):
    """Main dashboard view using Supabase REST API"""
    # Get items from Supabase
    in_progress = supabase_client.get_all_items(status='in_progress')
    done = supabase_client.get_all_items(status='done')
    
    context = {
        'in_progress': in_progress,
        'done': done,
    }
    return render(request, 'dashboard.html', context)

@csrf_exempt
@require_POST
def update_status(request):
    """Update billing item status via AJAX"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        new_status = data.get('status')
        
        # Update in Supabase
        success = supabase_client.update_item(item_id, {'status': new_status})
        
        if success:
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Update failed'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_POST
def create_item(request):
    """Create new billing item"""
    try:
        data = json.loads(request.body)
        
        # Create in Supabase
        item = supabase_client.create_item({
            'title': data.get('title'),
            'member_name': data.get('member_name'),
            'member_id': data.get('member_id'),
            'due_date': data.get('due_date'),
            'status': data.get('status', 'in_progress'),
            'tag_type': data.get('tag_type', 'SIGNED')
        })
        
        if item:
            return JsonResponse({'success': True, 'item_id': item.get('id')})
        else:
            return JsonResponse({'success': False, 'message': 'Creation failed'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)