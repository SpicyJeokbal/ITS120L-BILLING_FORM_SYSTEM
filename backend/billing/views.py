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
from django.contrib.auth import authenticate, update_session_auth_hash
import hashlib
import json
import re

def login_page(request):
    """Login page view with security"""
    print("\n=== LOGIN PAGE DEBUG ===")
    print(f"Request method: {request.method}")
    print(f"User authenticated: {request.user.is_authenticated}")
    print(f"Session key: {request.session.session_key}")

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
            
            # Log the user activity in Supabase with details
            full_name = user.first_name or username
            log_details = f"{full_name} logged in successfully"
            supabase_client.log_user_activity(user.username, 'login', log_details)
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')
    
    return render(request, 'login.html')

@login_required(login_url='login')
def check_user_role(request):
    """API endpoint to check current user's role"""
    try:
        user_profile = supabase_client.get_user_by_username(request.user.username)
        
        if user_profile:
            return JsonResponse({
                'success': True,
                'role': user_profile.get('role', 'librarian'),
                'status': user_profile.get('status', 'active'),
                'can_access': user_profile.get('can_access', True)
            })
        else:
            return JsonResponse({
                'success': False,
                'role': 'librarian'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

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
        
        # Check if username already exists in Supabase
        if supabase_client.get_user_by_username(username):
            errors.append('Username already taken.')
        
        # Check if email already exists in Supabase
        if supabase_client.get_user_by_email(email):
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
            # Hash the password
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Create Django user (still needed for sessions)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=full_name
            )
            
            # Store user info in Supabase with password hash
            supabase_client.create_user_profile({
                'username': username,
                'email': email,
                'full_name': full_name,
                'password_hash': password_hash,
                'created_at': user.date_joined.isoformat()
            })
            
            # Log the registration
            log_details = f"New user registered: {full_name} ({email})"
            supabase_client.log_user_activity(username, 'register', log_details)
            
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return render(request, 'register.html')
    
    return render(request, 'register.html')

def logout_view(request):
    """Logout view with activity logging"""
    username = request.user.username if request.user.is_authenticated else 'unknown'
    full_name = request.user.first_name if request.user.is_authenticated else username
    
    # Log logout activity with details
    log_details = f"{full_name} logged out"
    supabase_client.log_user_activity(username, 'logout', log_details)
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@csrf_exempt
@require_POST
@login_required(login_url='login')
def update_profile(request):
    """Update user profile (name and email)"""
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name')
        email = data.get('email')
        
        if not full_name or not email:
            return JsonResponse({
                'success': False,
                'message': 'Full name and email are required'
            }, status=400)
        
        # Validate email format (Mapua email)
        if not email.endswith('@mymail.mapua.edu.ph'):
            return JsonResponse({
                'success': False,
                'message': 'Email must be a valid Mapua email (@mymail.mapua.edu.ph)'
            }, status=400)
        
        # Check if email is already taken by another user
        existing_user = supabase_client.get_user_by_email(email)
        if existing_user and existing_user.get('username') != request.user.username:
            return JsonResponse({
                'success': False,
                'message': 'Email already registered to another user'
            }, status=400)
        
        # Update Django User
        request.user.first_name = full_name
        request.user.email = email
        request.user.save()
        
        # Update Supabase user_profiles
        endpoint = f"{supabase_client.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{request.user.username}'}
        update_data = {
            'full_name': full_name,
            'email': email,
            'updated_at': datetime.now().isoformat()
        }
        
        response = requests.patch(
            endpoint, 
            headers=supabase_client.headers, 
            params=params, 
            json=update_data
        )
        
        if response.status_code in [200, 204]:
            # Log the activity
            log_details = f"Updated profile: name={full_name}, email={email}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='update_profile',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update profile in database'
            }, status=500)
            
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def change_password(request):
    """Change user password"""
    try:
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        
        if not current_password or not new_password:
            return JsonResponse({
                'success': False,
                'message': 'Current and new password are required'
            }, status=400)
        
        # Validate new password strength
        if len(new_password) < 8:
            return JsonResponse({
                'success': False,
                'message': 'New password must be at least 8 characters'
            }, status=400)
        
        # Verify current password
        user = authenticate(username=request.user.username, password=current_password)
        if not user:
            return JsonResponse({
                'success': False,
                'message': 'Current password is incorrect'
            }, status=400)
        
        # Update Django User password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        # Update Supabase user_profiles password_hash
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        endpoint = f"{supabase_client.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{request.user.username}'}
        update_data = {
            'password_hash': password_hash,
            'updated_at': datetime.now().isoformat()
        }
        
        response = requests.patch(
            endpoint, 
            headers=supabase_client.headers, 
            params=params, 
            json=update_data
        )
        
        if response.status_code in [200, 204]:
            # Log the activity
            log_details = "Changed account password"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='change_password',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Password changed successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update password in database'
            }, status=500)
            
    except Exception as e:
        print(f"Error changing password: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


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
        
        # Get the item first to get details for logging
        item = supabase_client.get_item_by_id(item_id)
        
        # Update in Supabase
        success = supabase_client.update_item(item_id, {'status': new_status})
        
        if success:
            # Log the activity with details
            try:
                username = request.user.username if request.user.is_authenticated else 'anonymous'
                if item:
                    student_name = item.get('name', 'Unknown')
                    student_no = item.get('student_no', 'N/A')
                    log_details = f"Updated charge form #{item_id} status to '{new_status}' for {student_name} (Student No: {student_no})"
                else:
                    log_details = f"Updated charge form #{item_id} status to '{new_status}'"
                
                supabase_client.log_user_activity(
                    username=username,
                    activity_type='update_billing',
                    details=log_details
                )
            except Exception as log_error:
                print(f"Warning: Could not log activity: {str(log_error)}")
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'message': 'Update failed'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

@csrf_exempt
@require_POST
def create_item(request):
    """Create new billing item (legacy endpoint)"""
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

@csrf_exempt
@require_POST
def create_billing(request):
    """Create new billing/charge form"""
    try:
        # Parse request data
        data = json.loads(request.body)
        print(f"\n=== CREATE BILLING DEBUG ===")
        print(f"Received data: {json.dumps(data, indent=2)}")
        
        # Validate required fields
        required_fields = ['name', 'student_no', 'program', 'term', 'items', 'total']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            error_msg = f"Missing required fields: {', '.join(missing_fields)}"
            print(f"ERROR: {error_msg}")
            return JsonResponse({'success': False, 'message': error_msg}, status=400)
        
        # Get items
        items = data.get('items', [])
        if not items:
            return JsonResponse({'success': False, 'message': 'No items provided'}, status=400)
        
        # For now, we'll use the first item's details
        first_item = items[0]
        
        # Calculate total from all items
        total_amount = sum(item['quantity'] * item['amount'] for item in items)
        
        # Build items description
        items_description = ', '.join([f"{item['description']} (x{item['quantity']})" for item in items])
        
        # Create billing data matching your Supabase table structure
        billing_data = {
            'name': data.get('name'),
            'student_no': data.get('student_no'),
            'program_year': data.get('program'),
            'term': data.get('term'),
            'school_year': data.get('academic_year') or '2025-2026',
            'date': data.get('date'),
            'quantity': first_item.get('quantity', 1),
            'description': items_description,
            'amount': first_item.get('amount', 0),
            'total': total_amount,
            'status': data.get('status', 'in_progress'),
            'charged_by': data.get('charged_by'),
        }
        
        print(f"Billing data to save: {json.dumps(billing_data, indent=2)}")
        
        # Create in Supabase
        item = supabase_client.create_item(billing_data)
        
        if item:
            item_id = item.get('id')
            print(f"Successfully created item with ID: {item_id}")
            
            # Log the activity with detailed information
            try:
                username = request.user.username if request.user.is_authenticated else 'anonymous'
                student_name = data.get('name')
                student_no = data.get('student_no')
                charge_number = data.get('charge_number', item_id)
                
                # Create detailed log message
                log_details = f"Created charge form #{charge_number} for {student_name} (Student No: {student_no}) - Total: ₱{total_amount:.2f} - Items: {items_description}"
                
                supabase_client.log_user_activity(
                    username=username,
                    activity_type='create_billing',
                    details=log_details
                )
            except Exception as log_error:
                print(f"Warning: Could not log activity: {str(log_error)}")
            
            return JsonResponse({'success': True, 'item_id': item_id})
        else:
            print("ERROR: Supabase create_item returned None")
            return JsonResponse({'success': False, 'message': 'Failed to create item in database'}, status=400)
            
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON data: {str(e)}"
        print(f"ERROR: {error_msg}")
        return JsonResponse({'success': False, 'message': error_msg}, status=400)
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': error_msg}, status=500)

@login_required(login_url='login')
def get_billing(request, item_id):
    """Get a single billing item by ID"""
    try:
        print(f"\n=== GET BILLING DEBUG ===")
        print(f"Fetching item ID: {item_id}")
        
        # Get item from Supabase
        item = supabase_client.get_item_by_id(item_id)
        
        if item:
            print(f"Successfully fetched item: {item.get('id')}")
            return JsonResponse({'success': True, 'item': item})
        else:
            print(f"ERROR: Item not found with ID: {item_id}")
            return JsonResponse({'success': False, 'message': 'Item not found'}, status=404)
            
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'message': error_msg}, status=500)
    
@login_required(login_url='login')
def students_page(request):
    """Students management page"""
    return render(request, 'students.html')

@login_required(login_url='login')
def fees_page(request):
    """Fees and violations management page"""
    return render(request, 'fees.html')

@login_required(login_url='login')
def logs_page(request):
    """Activity logs page"""
    return render(request, 'logs.html')

@login_required(login_url='login')
def logs_api(request):
    """API endpoint to get activity logs from Supabase"""
    try:
        # Get logs from Supabase
        logs = supabase_client.get_all_logs()
        
        return JsonResponse({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required(login_url='login')
def archive_page(request):
    """Archive page for old billing forms"""
    return render(request, 'archive.html')

@csrf_exempt
@require_POST
def upload_students(request):
    """Upload students from Excel file"""
    return JsonResponse({'success': False, 'message': 'Not implemented yet'})

@csrf_exempt
@require_POST
def add_student(request):
    """Add a single student manually"""
    return JsonResponse({'success': False, 'message': 'Not implemented yet'})

@csrf_exempt
def get_student(request):
    """Get student info by student number"""
    return JsonResponse({'success': False, 'message': 'Not implemented yet'})

@csrf_exempt
@require_POST
def add_fee(request):
    """Add a fee or violation"""
    return JsonResponse({'success': False, 'message': 'Not implemented yet'})

@csrf_exempt
@require_POST
def delete_fee(request):
    """Delete a fee or violation"""
    return JsonResponse({'success': False, 'message': 'Not implemented yet'})