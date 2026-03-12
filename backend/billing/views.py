# backend/billing/views.py
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
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
from datetime import datetime
import hashlib
from django.shortcuts import render
import json
import re
import requests

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
    awaiting_approval = supabase_client.get_all_items(status='awaiting_approval')
    in_progress = supabase_client.get_all_items(status='in_progress')
    done = supabase_client.get_all_items(status='done')
    
    context = {
        'awaiting_approval': awaiting_approval,
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
        
        print(f"\n=== UPDATE STATUS DEBUG ===")
        print(f"Item ID: {item_id}")
        print(f"New status: {new_status}")
        print(f"User: {request.user.username}")
        
        # Get the item first to get details for logging
        item = supabase_client.get_item_by_id(item_id)
        
        # Prepare update data
        update_data = {'status': new_status}
        
        # If approving form (moving from awaiting_approval to in_progress),
        # add librarian signature and update charged_by
        if new_status == 'in_progress' and item and item.get('status') == 'awaiting_approval':
            print("✅ Approving form - adding librarian signature")
            
            # Get current user's signature from user_profiles
            user_profile = supabase_client.get_user_by_username(request.user.username)
            
            if user_profile and user_profile.get('librarian_signature'):
                update_data['librarian_signature'] = user_profile.get('librarian_signature')
                print(f"✅ Found librarian signature for {request.user.username}")
            else:
                print(f"⚠️ No signature found for {request.user.username}")
            
            # Update charged_by to current user if it's "Student Submission"
            if item.get('charged_by') == 'Student Submission' or not item.get('charged_by'):
                charged_by_name = request.user.first_name or request.user.username
                update_data['charged_by'] = charged_by_name
                print(f"✅ Updated charged_by to {charged_by_name}")
        
        print(f"Update data: {update_data}")
        
        # Update in Supabase
        success = supabase_client.update_item(item_id, update_data)
        
        if success:
            print("✅ Successfully updated item")
            
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
            print("❌ Failed to update item")
            return JsonResponse({'success': False, 'message': 'Update failed'}, status=400)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
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
        print(f"Received data keys: {list(data.keys())}")
        print(f"Librarian signature present: {'librarian_signature' in data}")
        if 'librarian_signature' in data:
            sig = data.get('librarian_signature')
            print(f"Signature length: {len(sig) if sig else 0}")
            print(f"Signature starts with: {sig[:50] if sig else 'None'}...")
        
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
        
        # Get librarian name (should be from logged-in user)
        charged_by = data.get('charged_by')
        
        # If charged_by is empty or "Student Submission", use current user's name
        if not charged_by or charged_by == 'Student Submission':
            if request.user.is_authenticated:
                charged_by = request.user.first_name or request.user.username
            else:
                charged_by = 'Admin'
        
        # Get librarian signature if provided
        librarian_signature = data.get('librarian_signature')
        
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
            'charged_by': charged_by,
        }
        
        # Add librarian signature if provided
        if librarian_signature:
            billing_data['librarian_signature'] = librarian_signature
            print(f"✅ Librarian signature included in billing_data")
        else:
            print(f"⚠️ No librarian signature provided")
        
        print(f"Billing data to save (excluding signature): {json.dumps({k: v for k, v in billing_data.items() if k != 'librarian_signature'}, indent=2)}")
        
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

@csrf_exempt 
@login_required(login_url='login')
def delete_billing(request, item_id):
    """Delete a billing form permanently"""
    try:
        print(f"\n=== DELETE BILLING DEBUG ===")
        print(f"Deleting item ID: {item_id}")
        
        # Get item details for logging before deletion
        item = supabase_client.get_item_by_id(item_id)
        
        if not item:
            return JsonResponse({
                'success': False,
                'message': 'Billing form not found'
            }, status=404)
        
        # Delete the item from Supabase
        success = supabase_client.delete_item(item_id)
        
        if success:
            print(f"✅ Successfully deleted item {item_id}")
            
            # Log the activity
            try:
                username = request.user.username if request.user.is_authenticated else 'anonymous'
                student_name = item.get('name', 'Unknown')
                student_no = item.get('student_no', 'N/A')
                log_details = f"Deleted charge form #{item_id} for {student_name} (Student No: {student_no})"
                
                supabase_client.log_user_activity(
                    username=username,
                    activity_type='delete_billing',
                    details=log_details
                )
            except Exception as log_error:
                print(f"Warning: Could not log activity: {str(log_error)}")
            
            return JsonResponse({
                'success': True,
                'message': 'Billing form deleted successfully'
            })
        else:
            print(f"❌ Failed to delete item {item_id}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to delete billing form'
            }, status=500)
            
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': error_msg
        }, status=500)

    
@login_required(login_url='login')
def students_page(request):
    """Student management page"""
    # Get all students from Supabase
    students = supabase_client.get_all_students()
    
    context = {
        'students': students
    }
    return render(request, 'students.html', context)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def upload_students(request):
    """Import students from Excel (uploaded as JSON)"""
    try:
        data = json.loads(request.body)
        students = data.get('students', [])
        
        if not students:
            return JsonResponse({
                'success': False,
                'message': 'No student data provided'
            }, status=400)
        
        # Validate and import students
        imported = 0
        errors = []
        
        for student in students:
            # Validate required fields
            if not student.get('student_no') or not student.get('name'):
                errors.append(f"Missing required fields for student: {student}")
                continue
            
            # Create or update student in Supabase
            success = supabase_client.create_or_update_student(student)
            if success:
                imported += 1
            else:
                errors.append(f"Failed to import: {student.get('name')}")
        
        # Log the activity
        log_details = f"Imported {imported} students from Excel"
        supabase_client.log_user_activity(
            username=request.user.username,
            activity_type='import_students',
            details=log_details
        )
        
        return JsonResponse({
            'success': True,
            'imported': imported,
            'errors': errors
        })
        
    except Exception as e:
        print(f"Error importing students: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def add_student(request):
    """Add or update a single student"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['student_no', 'name', 'program', 'term', 'academic_year']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return JsonResponse({
                'success': False,
                'message': f"Missing required fields: {', '.join(missing_fields)}"
            }, status=400)
        
        # Check if this is an update (original_student_no present)
        original_student_no = data.get('original_student_no')
        is_update = bool(original_student_no)
        
        # If updating and student number changed, check if new number already exists
        if is_update and original_student_no != data['student_no']:
            existing = supabase_client.get_student_by_number(data['student_no'])
            if existing:
                return JsonResponse({
                    'success': False,
                    'message': 'Student number already exists'
                }, status=400)
        
        # Create student data
        student_data = {
            'student_no': data['student_no'],
            'name': data['name'],
            'program': data['program'],
            'term': data['term'],
            'academic_year': data['academic_year'],
            'updated_at': datetime.now().isoformat()
        }
        
        if is_update:
            # Update existing student
            success = supabase_client.update_student(original_student_no, student_data)
            action = 'updated'
        else:
            # Check if student already exists
            existing = supabase_client.get_student_by_number(data['student_no'])
            if existing:
                return JsonResponse({
                    'success': False,
                    'message': 'Student number already exists'
                }, status=400)
            
            # Create new student
            student_data['created_at'] = datetime.now().isoformat()
            success = supabase_client.create_student(student_data)
            action = 'added'
        
        if success:
            # Log the activity
            log_details = f"{action.capitalize()} student: {data['name']} ({data['student_no']})"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type=f'{action}_student',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Student {action} successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': f'Failed to {action} student'
            }, status=500)
            
    except Exception as e:
        print(f"Error adding/updating student: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def delete_student(request):
    """Delete a student"""
    try:
        data = json.loads(request.body)
        student_no = data.get('student_no')
        
        if not student_no:
            return JsonResponse({
                'success': False,
                'message': 'Student number required'
            }, status=400)
        
        # Get student info for logging
        student = supabase_client.get_student_by_number(student_no)
        if not student:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
        
        # Delete student
        success = supabase_client.delete_student(student_no)
        
        if success:
            # Log the activity
            log_details = f"Deleted student: {student.get('name')} ({student_no})"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='delete_student',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Student deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to delete student'
            }, status=500)
            
    except Exception as e:
        print(f"Error deleting student: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def get_student(request):
    """Get student details by student number"""
    try:
        data = json.loads(request.body)
        student_no = data.get('student_no')
        
        if not student_no:
            return JsonResponse({
                'success': False,
                'message': 'Student number required'
            }, status=400)
        
        student = supabase_client.get_student_by_number(student_no)
        
        if student:
            return JsonResponse({
                'success': True,
                'student': student
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Student not found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

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
def list_students_api(request):
    """API endpoint to get all students for autocomplete"""
    try:
        students = supabase_client.get_all_students()
        
        students_data = [{
            'student_no': s.get('student_no'),
            'name': s.get('name'),
            'program': s.get('program'),
            'term': s.get('term'),
            'academic_year': s.get('academic_year')
        } for s in students]
        
        return JsonResponse({
            'success': True,
            'students': students_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'students': []
        }, status=500)
    
#ADMIN SIGNATURE
@login_required(login_url='login')
def signature_settings_page(request):
    """Signature settings page for librarians"""
    try:
        # Get current user's profile from Supabase
        user_profile = supabase_client.get_user_by_username(request.user.username)
        
        has_signature = False
        current_signature = None
        
        if user_profile and user_profile.get('librarian_signature'):
            has_signature = True
            current_signature = user_profile.get('librarian_signature')
        
        context = {
            'has_signature': has_signature,
            'current_signature': current_signature
        }
        
        return render(request, 'signature_settings.html', context)
        
    except Exception as e:
        print(f"Error loading signature settings: {str(e)}")
        context = {
            'has_signature': False,
            'current_signature': None
        }
        return render(request, 'signature_settings.html', context)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def save_librarian_signature(request):
    """Save librarian's signature"""
    try:
        # Get signature file
        signature_file = request.FILES.get('signature')
        
        if not signature_file:
            return JsonResponse({
                'success': False,
                'message': 'Signature file required'
            }, status=400)
        
        # Validate file size (max 100KB)
        if signature_file.size > 100 * 1024:
            return JsonResponse({
                'success': False,
                'message': 'Signature file too large (max 100KB)'
            }, status=400)
        
        # Validate file type
        if not signature_file.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'message': 'Invalid file type. Must be an image.'
            }, status=400)
        
        # Convert to base64 for storage
        import base64
        signature_data = signature_file.read()
        signature_base64 = f"data:{signature_file.content_type};base64,{base64.b64encode(signature_data).decode('utf-8')}"
        
        # Update user profile in Supabase
        success = supabase_client.update_librarian_signature(
            request.user.username,
            signature_base64
        )
        
        if success:
            # Log the activity
            log_details = f"Updated librarian signature"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='update_signature',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Signature saved successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to save signature'
            }, status=500)
            
    except Exception as e:
        print(f"Error saving signature: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required(login_url='login')
def get_librarian_signature(request):
    """API endpoint to get current user's signature"""
    try:
        user_profile = supabase_client.get_user_by_username(request.user.username)
        
        if user_profile and user_profile.get('librarian_signature'):
            return JsonResponse({
                'success': True,
                'signature': user_profile.get('librarian_signature')
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'No signature found'
            }, status=404)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    
#FEES
@login_required(login_url='login')
def fees_page(request):
    """Fees and violations management page"""
    try:
        # Get all fees from Supabase
        fees = supabase_client.get_all_fees()
        
        context = {
            'fees': fees
        }
        return render(request, 'fees.html', context)
    except Exception as e:
        print(f"Error loading fees page: {str(e)}")
        context = {'fees': []}
        return render(request, 'fees.html', context)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def add_fee(request):
    """Add a new fee or violation"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('name'):
            return JsonResponse({
                'success': False,
                'message': 'Fee name is required'
            }, status=400)
        
        if not data.get('amount'):
            return JsonResponse({
                'success': False,
                'message': 'Amount is required'
            }, status=400)
        
        # Validate amount
        try:
            amount = float(data.get('amount'))
            if amount < 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Amount must be a positive number'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid amount format'
            }, status=400)
        
        # Create fee data
        fee_data = {
            'name': data.get('name').strip(),
            'description': data.get('description', '').strip(),
            'amount': amount,
            'created_at': datetime.now().isoformat(),
            'created_by': request.user.username
        }
        
        # Add to Supabase
        success = supabase_client.create_fee(fee_data)
        
        if success:
            # Log the activity
            log_details = f"Added new fee: {fee_data['name']} - ₱{amount:.2f}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='create_fee',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Fee added successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to add fee'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error adding fee: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def update_fee(request):
    """Update an existing fee"""
    try:
        data = json.loads(request.body)
        
        fee_id = data.get('id')
        if not fee_id:
            return JsonResponse({
                'success': False,
                'message': 'Fee ID is required'
            }, status=400)
        
        # Validate required fields
        if not data.get('name'):
            return JsonResponse({
                'success': False,
                'message': 'Fee name is required'
            }, status=400)
        
        if not data.get('amount'):
            return JsonResponse({
                'success': False,
                'message': 'Amount is required'
            }, status=400)
        
        # Validate amount
        try:
            amount = float(data.get('amount'))
            if amount < 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Amount must be a positive number'
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid amount format'
            }, status=400)
        
        # Update fee data
        fee_data = {
            'name': data.get('name').strip(),
            'description': data.get('description', '').strip(),
            'amount': amount,
            'updated_at': datetime.now().isoformat(),
            'updated_by': request.user.username
        }
        
        # Update in Supabase
        success = supabase_client.update_fee(fee_id, fee_data)
        
        if success:
            # Log the activity
            log_details = f"Updated fee: {fee_data['name']} - ₱{amount:.2f}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='update_fee',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Fee updated successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to update fee'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error updating fee: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_POST
@login_required(login_url='login')
def delete_fee(request):
    """Delete a fee or violation"""
    try:
        data = json.loads(request.body)
        
        fee_id = data.get('id')
        if not fee_id:
            return JsonResponse({
                'success': False,
                'message': 'Fee ID is required'
            }, status=400)
        
        # Get fee info for logging
        fee = supabase_client.get_fee_by_id(fee_id)
        if not fee:
            return JsonResponse({
                'success': False,
                'message': 'Fee not found'
            }, status=404)
        
        # Delete fee
        success = supabase_client.delete_fee(fee_id)
        
        if success:
            # Log the activity
            log_details = f"Deleted fee: {fee.get('name')} - ₱{fee.get('amount', 0):.2f}"
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='delete_fee',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Fee deleted successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to delete fee'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print(f"Error deleting fee: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    
@login_required(login_url='login')
def list_fees_api(request):
    """API endpoint to get all fees for billing form dropdown"""
    try:
        fees = supabase_client.get_all_fees()
        
        fees_data = [{
            'id': f.get('id'),
            'name': f.get('name'),
            'description': f.get('description'),
            'amount': float(f.get('amount', 0))
        } for f in fees]
        
        return JsonResponse({
            'success': True,
            'fees': fees_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'fees': []
        }, status=500)
    

""" ARCHIVED """
@login_required(login_url='login')
def archive_page(request):
    """Archive page showing all archived forms"""
    # Get archived items
    archived_items = supabase_client.get_archived_items()
    
    context = {
        'archived_items': archived_items
    }
    return render(request, 'archive.html', context)

@csrf_exempt
@require_POST
@login_required(login_url='login')
def archive_form(request):
    """Archive a billing form"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        if not item_id:
            return JsonResponse({
                'success': False,
                'message': 'Item ID required'
            }, status=400)
        
        # Get item details for logging
        item = supabase_client.get_item_by_id(item_id)
        
        # Archive the item
        success = supabase_client.archive_item(item_id, request.user.username)
        
        if success:
            # Log the activity
            if item:
                log_details = f"Archived charge form #{item_id} for {item.get('name', 'Unknown')} (Student No: {item.get('student_no', 'N/A')})"
            else:
                log_details = f"Archived charge form #{item_id}"
            
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='archive_form',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Form archived successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to archive form'
            }, status=500)
    
    except Exception as e:
        print(f"Error archiving form: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@login_required(login_url='login')
def restore_from_archive(request):
    """Restore an archived form back to in_progress"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        if not item_id:
            return JsonResponse({
                'success': False,
                'message': 'Item ID required'
            }, status=400)
        
        # Get item details for logging
        item = supabase_client.get_item_by_id(item_id)
        
        # Restore the item
        success = supabase_client.restore_from_archive(item_id)
        
        if success:
            # Log the activity
            if item:
                log_details = f"Restored charge form #{item_id} from archive for {item.get('name', 'Unknown')} (Student No: {item.get('student_no', 'N/A')})"
            else:
                log_details = f"Restored charge form #{item_id} from archive"
            
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='restore_form',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Form restored successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to restore form'
            }, status=500)
    
    except Exception as e:
        print(f"Error restoring form: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_POST
@login_required(login_url='login')
def delete_archived_form(request):
    """Permanently delete an archived form"""
    try:
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        if not item_id:
            return JsonResponse({
                'success': False,
                'message': 'Item ID required'
            }, status=400)
        
        # Get item details for logging before deletion
        item = supabase_client.get_item_by_id(item_id)
        
        # Check if item is archived
        if item and item.get('status') != 'archived':
            return JsonResponse({
                'success': False,
                'message': 'Can only delete archived forms'
            }, status=400)
        
        # Delete the item
        success = supabase_client.delete_archived_item(item_id)
        
        if success:
            # Log the activity
            if item:
                log_details = f"Permanently deleted archived form #{item_id} for {item.get('name', 'Unknown')} (Student No: {item.get('student_no', 'N/A')})"
            else:
                log_details = f"Permanently deleted archived form #{item_id}"
            
            supabase_client.log_user_activity(
                username=request.user.username,
                activity_type='delete_archived_form',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Form permanently deleted'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Failed to delete form'
            }, status=500)
    
    except Exception as e:
        print(f"Error deleting form: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required(login_url='login')
def run_auto_archive(request):
    """Manual endpoint to trigger auto-archive (can be called by cron)"""
    try:
        result = supabase_client.auto_archive_old_forms(days=30)
        
        if result.get('success'):
            # Log the activity
            log_details = f"Auto-archived {result['archived_count']} forms older than 30 days (found {result['total_found']} eligible forms)"
            
            supabase_client.log_user_activity(
                username='system',
                activity_type='auto_archive',
                details=log_details
            )
            
            return JsonResponse({
                'success': True,
                'archived_count': result['archived_count'],
                'total_found': result['total_found'],
                'message': f"Successfully archived {result['archived_count']} forms"
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('error', 'Auto-archive failed')
            }, status=500)
    
    except Exception as e:
        print(f"Error in auto-archive: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    

@login_required(login_url='login')
def export_to_excel(request):
    """Export all billing forms to Excel"""
    try:
        # Get ALL items (all statuses including archived)
        awaiting = supabase_client.get_all_items(status='awaiting_approval')
        in_progress = supabase_client.get_all_items(status='in_progress')
        done = supabase_client.get_all_items(status='done')
        archived = supabase_client.get_archived_items()
        
        # Combine all items
        all_items = awaiting + in_progress + done + archived
        
        # Create workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "Billing Forms"
        
        # Define headers
        headers = [
            'ID', 'Date', 'Student Name', 'Student No', 'Program', 'Term', 
            'School Year', 'Description', 'Quantity', 'Amount', 'Total', 
            'Status', 'Charged By', 'Archived Date', 'Archived By'
        ]
        
        # Style for headers
        header_fill = PatternFill(start_color="0052CC", end_color="0052CC", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        
        # Write headers
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = header_alignment
        
        # Border style
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Write data
        for row_num, item in enumerate(all_items, 2):
            # Format date
            date_str = item.get('date', '')
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    date_str = date_obj.strftime('%m/%d/%Y')
                except:
                    pass
            
            # Format archived date
            archived_date = item.get('archived_at', '')
            if archived_date:
                try:
                    archived_obj = datetime.strptime(archived_date.split('T')[0], '%Y-%m-%d')
                    archived_date = archived_obj.strftime('%m/%d/%Y %I:%M %p')
                except:
                    pass
            
            row_data = [
                item.get('id', ''),
                date_str,
                item.get('name', ''),
                item.get('student_no', ''),
                item.get('program_year', ''),
                item.get('term', ''),
                item.get('school_year', ''),
                item.get('description', ''),
                item.get('quantity', ''),
                f"₱{float(item.get('amount', 0)):.2f}",
                f"₱{float(item.get('total', 0)):.2f}",
                item.get('status', '').upper(),
                item.get('charged_by', ''),
                archived_date,
                item.get('archived_by', '')
            ]
            
            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                
                # Color code by status
                if col_num == 12:  # Status column
                    status = item.get('status', '')
                    if status == 'awaiting_approval':
                        cell.fill = PatternFill(start_color="FFF0B3", end_color="FFF0B3", fill_type="solid")
                    elif status == 'in_progress':
                        cell.fill = PatternFill(start_color="E3FCEF", end_color="E3FCEF", fill_type="solid")
                    elif status == 'done':
                        cell.fill = PatternFill(start_color="DEEBFF", end_color="DEEBFF", fill_type="solid")
                    elif status == 'archived':
                        cell.fill = PatternFill(start_color="F4F5F7", end_color="F4F5F7", fill_type="solid")
        
        # Adjust column widths
        column_widths = {
            'A': 8,   # ID
            'B': 12,  # Date
            'C': 25,  # Student Name
            'D': 15,  # Student No
            'E': 10,  # Program
            'F': 8,   # Term
            'G': 12,  # School Year
            'H': 40,  # Description
            'I': 10,  # Quantity
            'J': 12,  # Amount
            'K': 12,  # Total
            'L': 15,  # Status
            'M': 20,  # Charged By
            'N': 18,  # Archived Date
            'O': 15   # Archived By
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Freeze header row
        ws.freeze_panes = 'A2'
        
        # Add summary at the top (insert rows)
        ws.insert_rows(1, 3)
        
        # Title
        ws.merge_cells('A1:O1')
        title_cell = ws['A1']
        title_cell.value = 'MAPUA LIBRARY BILLING FORMS REPORT'
        title_cell.font = Font(bold=True, size=14, color="0052CC")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Summary
        ws.merge_cells('A2:O2')
        summary_cell = ws['A2']
        summary_cell.value = f'Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")} | Total Forms: {len(all_items)} | Awaiting: {len(awaiting)} | In Progress: {len(in_progress)} | Done: {len(done)} | Archived: {len(archived)}'
        summary_cell.font = Font(size=10, color="5E6C84")
        summary_cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Empty row for spacing
        ws.row_dimensions[3].height = 5
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Log the activity
        log_details = f"Exported {len(all_items)} billing forms to Excel"
        supabase_client.log_user_activity(
            username=request.user.username,
            activity_type='export_excel',
            details=log_details
        )
        
        # Create response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=billing_forms_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return response
        
    except Exception as e:
        print(f"Error exporting to Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required(login_url='login')
def export_to_pdf(request):
    """Export all billing forms to PDF"""
    try:
        # Get ALL items
        awaiting = supabase_client.get_all_items(status='awaiting_approval')
        in_progress = supabase_client.get_all_items(status='in_progress')
        done = supabase_client.get_all_items(status='done')
        archived = supabase_client.get_archived_items()
        
        all_items = awaiting + in_progress + done + archived
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Container for elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#0052CC'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#5E6C84'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#172B4D'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        )
        
        # Title
        title = Paragraph('MAPUA LIBRARY BILLING FORMS REPORT', title_style)
        elements.append(title)
        
        # Subtitle with summary
        subtitle_text = f'''
        Generated: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}<br/>
        Total Forms: {len(all_items)} | 
        Awaiting Approval: {len(awaiting)} | 
        In Progress: {len(in_progress)} | 
        Done: {len(done)} | 
        Archived: {len(archived)}
        '''
        subtitle = Paragraph(subtitle_text, subtitle_style)
        elements.append(subtitle)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary Statistics
        summary_heading = Paragraph('Summary Statistics', heading_style)
        elements.append(summary_heading)
        
        # Calculate totals
        total_amount = sum(float(item.get('total', 0)) for item in all_items)
        awaiting_total = sum(float(item.get('total', 0)) for item in awaiting)
        in_progress_total = sum(float(item.get('total', 0)) for item in in_progress)
        done_total = sum(float(item.get('total', 0)) for item in done)
        archived_total = sum(float(item.get('total', 0)) for item in archived)
        
        # Summary table
        summary_data = [
            ['Status', 'Count', 'Total Amount'],
            ['Awaiting Approval', str(len(awaiting)), f'PHP{awaiting_total:,.2f}'],
            ['In Progress', str(len(in_progress)), f'PHP{in_progress_total:,.2f}'],
            ['Done', str(len(done)), f'PHP{done_total:,.2f}'],
            ['Archived', str(len(archived)), f'PHP{archived_total:,.2f}'],
            ['TOTAL', str(len(all_items)), f'PHP{total_amount:,.2f}']
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0052CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F4F5F7')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DFE1E6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F9F9F9')])
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Detailed Forms List
        forms_heading = Paragraph('Detailed Forms List', heading_style)
        elements.append(forms_heading)
        
        # Group by status
        status_groups = {
            'Awaiting Approval': awaiting,
            'In Progress': in_progress,
            'Done': done,
            'Archived': archived
        }
        
        for status_name, items in status_groups.items():
            if not items:
                continue
            
            # Status subheading
            status_para = Paragraph(f'<b>{status_name}</b> ({len(items)} forms)', styles['Heading3'])
            elements.append(status_para)
            elements.append(Spacer(1, 0.1*inch))
            
            # Create table for this status
            table_data = [['Date', 'Student Name', 'Student No', 'Description', 'Total']]
            
            for item in items[:50]:  # Limit to 50 per status to avoid huge PDFs
                date_str = item.get('date', '')
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        date_str = date_obj.strftime('%m/%d/%Y')
                    except:
                        pass
                
                description = item.get('description', '')[:40] + '...' if len(item.get('description', '')) > 40 else item.get('description', '')
                
                table_data.append([
                    date_str,
                    item.get('name', '')[:20],
                    item.get('student_no', ''),
                    description,
                    f"PHP{float(item.get('total', 0)):,.2f}"
                ])
            
            # Create table
            status_table = Table(table_data, colWidths=[1*inch, 1.5*inch, 1*inch, 2*inch, 1*inch])
            
            # Table style based on status
            if status_name == 'Awaiting Approval':
                header_color = colors.HexColor('#FF991F')
            elif status_name == 'In Progress':
                header_color = colors.HexColor('#00875A')
            elif status_name == 'Done':
                header_color = colors.HexColor('#0052CC')
            else:
                header_color = colors.HexColor('#5E6C84')
            
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), header_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (4, 0), (4, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DFE1E6')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')])
            ]))
            
            elements.append(status_table)
            
            if len(items) > 50:
                remaining = Paragraph(f'<i>...and {len(items) - 50} more forms</i>', styles['Italic'])
                elements.append(remaining)
            
            elements.append(Spacer(1, 0.2*inch))
        
        # Footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#5E6C84'),
            alignment=TA_CENTER
        )
        footer_text = f'Generated by {request.user.first_name or request.user.username} | Mapua Library Billing System'
        footer = Paragraph(footer_text, footer_style)
        elements.append(Spacer(1, 0.3*inch))
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        # Log the activity
        log_details = f"Exported {len(all_items)} billing forms to PDF"
        supabase_client.log_user_activity(
            username=request.user.username,
            activity_type='export_pdf',
            details=log_details
        )
        
        # Get the value from the BytesIO buffer
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=billing_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error exporting to PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


