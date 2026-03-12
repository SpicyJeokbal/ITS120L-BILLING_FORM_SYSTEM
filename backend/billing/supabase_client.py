# backend/billing/supabase_client.py
import requests
from django.conf import settings
from datetime import datetime

class SupabaseClient:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_SERVICE_KEY
        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
    
    def get_all_items(self, status=None):
        """Get all billing items, optionally filtered by status"""
        endpoint = f"{self.url}/rest/v1/billing_items"
        params = {'order': 'created_at.desc'}
        
        if status:
            params['status'] = f'eq.{status}'
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    
    def get_item_by_id(self, item_id):
        """Get a single billing item by ID"""
        endpoint = f"{self.url}/rest/v1/billing_items"
        params = {'id': f'eq.{item_id}'}
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            items = response.json()
            return items[0] if items else None
        return None
    
    def create_item(self, data):
        """Create a new billing item"""
        endpoint = f"{self.url}/rest/v1/billing_items"
        response = requests.post(endpoint, headers=self.headers, json=data)
        if response.status_code == 201:
            return response.json()[0] if response.json() else None
        return None
    
    def update_item(self, item_id, data):
        """Update a billing item"""
        endpoint = f"{self.url}/rest/v1/billing_items"
        params = {'id': f'eq.{item_id}'}
        response = requests.patch(endpoint, headers=self.headers, params=params, json=data)
        return response.status_code == 200
    
    def delete_item(self, item_id):
        """Delete a billing item"""
        endpoint = f"{self.url}/rest/v1/billing_items"
        params = {'id': f'eq.{item_id}'}
        
        try:
            print(f"Attempting to delete item {item_id}")
            print(f"Endpoint: {endpoint}")
            print(f"Params: {params}")
            
            response = requests.delete(endpoint, headers=self.headers, params=params)
            
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 204:
                print(f"Item {item_id} deleted successfully")
                return True
            elif response.status_code == 200:
                print(f"Item {item_id} deleted successfully (200)")
                return True
            else:
                print(f"Delete failed - Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Exception during delete: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_user_profile(self, data):
        """Store user profile in Supabase"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            return response.status_code == 201
        except Exception as e:
            print(f"Error creating user profile: {e}")
            return False
    
    def get_user_by_username(self, username):
        """Get user profile by username"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{username}'}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user profile by email"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'email': f'eq.{email}'}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                users = response.json()
                return users[0] if users else None
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def log_user_activity(self, username, activity_type, details=None):
        """Log user activity (login/logout/actions) in Supabase"""
        endpoint = f"{self.url}/rest/v1/user_activity_logs"
        data = {
            'username': username,
            'activity_type': activity_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            return response.status_code == 201
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False
    
    def get_all_logs(self, limit=100):
        """Get all activity logs, ordered by most recent"""
        endpoint = f"{self.url}/rest/v1/user_activity_logs"
        params = {
            'order': 'timestamp.desc',
            'limit': limit
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        return []
    
      # =================== USER MANAGEMENT (HEAD LIBRARIAN) ===================
    
    def get_all_users(self):
        """Get all user profiles for user management"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'order': 'created_at.desc'}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def update_user_status(self, username, status):
        """Update user status (active/suspended/inactive)"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{username}'}
        
        # Set can_access based on status
        can_access = status == 'active'
        
        data = {
            'status': status,
            'can_access': can_access,
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            response = requests.patch(endpoint, headers=self.headers, params=params, json=data)
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error updating user status: {e}")
            return False
    
    def update_user_role(self, username, role):
        """Update user role (head_librarian/librarian/assistant)"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{username}'}
        
        data = {
            'role': role,
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            response = requests.patch(endpoint, headers=self.headers, params=params, json=data)
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
    
    def reset_user_password(self, username, new_password_hash):
        """Reset user password (hash should be provided)"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{username}'}
        
        data = {
            'password_hash': new_password_hash,
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            response = requests.patch(endpoint, headers=self.headers, params=params, json=data)
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error resetting password: {e}")
            return False
    
    def delete_user(self, username):
        """Delete user account (use with caution!)"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{username}'}
        try:
            response = requests.delete(endpoint, headers=self.headers, params=params)
            # Supabase returns 204 normally, or 200 with 'Prefer: return=representation'
            if response.status_code in [200, 204]:
                print(f"User {username} deleted successfully (status: {response.status_code})")
                return True
            else:
                print(f"Delete failed - Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def create_user_by_admin(self, user_data):
        """Create new user account by head librarian"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        
        # Ensure required fields
        from datetime import datetime
        user_data['created_at'] = datetime.now().isoformat()
        user_data['updated_at'] = datetime.now().isoformat()
        user_data['status'] = user_data.get('status', 'active')
        user_data['can_access'] = user_data.get('can_access', True)
        user_data['role'] = user_data.get('role', 'librarian')
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=user_data)
            if response.status_code == 201:
                data = response.json()
                return data[0] if isinstance(data, list) and data else data
            return None
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
        

     # =================== STUDENT MANAGEMENT ===================
    
    def get_all_students(self):
        """Get all students"""
        endpoint = f"{self.url}/rest/v1/students"
        params = {'order': 'created_at.desc'}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error getting students: {e}")
            return []
    
    def get_student_by_number(self, student_no):
        """Get student by student number"""
        endpoint = f"{self.url}/rest/v1/students"
        params = {'student_no': f'eq.{student_no}'}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                students = response.json()
                return students[0] if students else None
            return None
        except Exception as e:
            print(f"Error getting student: {e}")
            return None
    
    def create_student(self, student_data):
        """Create a new student"""
        endpoint = f"{self.url}/rest/v1/students"
        
        try:
            response = requests.post(endpoint, headers=self.headers, json=student_data)
            if response.status_code == 201:
                return True
            print(f"Failed to create student: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"Error creating student: {e}")
            return False
    
    def update_student(self, student_no, student_data):
        """Update existing student"""
        endpoint = f"{self.url}/rest/v1/students"
        params = {'student_no': f'eq.{student_no}'}
        
        try:
            response = requests.patch(endpoint, headers=self.headers, params=params, json=student_data)
            if response.status_code in [200, 204]:
                return True
            print(f"Failed to update student: {response.status_code} - {response.text}")
            return False
        except Exception as e:
            print(f"Error updating student: {e}")
            return False
    
    def delete_student(self, student_no):
        """Delete a student"""
        endpoint = f"{self.url}/rest/v1/students"
        params = {'student_no': f'eq.{student_no}'}
        
        try:
            response = requests.delete(endpoint, headers=self.headers, params=params)
            if response.status_code in [200, 204]:
                print(f"Student {student_no} deleted successfully")
                return True
            print(f"Delete failed - Status: {response.status_code}")
            return False
        except Exception as e:
            print(f"Error deleting student: {e}")
            return False
    
    def create_or_update_student(self, student_data):
        """Create student or update if exists (for Excel import)"""
        existing = self.get_student_by_number(student_data['student_no'])
        
        if existing:
            return self.update_student(student_data['student_no'], student_data)
        else:
            student_data['created_at'] = datetime.now().isoformat()
            return self.create_student(student_data)
        
    def update_librarian_signature(self, username, signature_base64):
        """Update librarian's signature in user_profiles"""
        endpoint = f"{self.url}/rest/v1/user_profiles"
        params = {'username': f'eq.{username}'}
        
        data = {
            'librarian_signature': signature_base64,
            'updated_at': datetime.now().isoformat()
        }
        
        try:
            response = requests.patch(endpoint, headers=self.headers, params=params, json=data)
            if response.status_code in [200, 204]:
                print(f"Signature updated for {username}")
                return True
            else:
                print(f"Failed to update signature: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error updating signature: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    
    # =================== FEE MANAGEMENT ===================
    
    def get_all_fees(self):
        """Get all fees"""
        endpoint = f"{self.url}/rest/v1/fees"
        params = {'order': 'created_at.desc'}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting fees: {response.status_code} - {response.text}")
            return []
        except Exception as e:
            print(f"Error getting fees: {e}")
            return []
    
    def get_fee_by_id(self, fee_id):
        """Get fee by ID"""
        endpoint = f"{self.url}/rest/v1/fees"
        params = {'id': f'eq.{fee_id}'}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            if response.status_code == 200:
                fees = response.json()
                return fees[0] if fees else None
            else:
                print(f"Error getting fee: {response.status_code} - {response.text}")
            return None
        except Exception as e:
            print(f"Error getting fee: {e}")
            return None
    
    def create_fee(self, fee_data):
        """Create a new fee"""
        endpoint = f"{self.url}/rest/v1/fees"
        
        try:
            print(f"Creating fee: {fee_data}")
            response = requests.post(endpoint, headers=self.headers, json=fee_data)
            
            if response.status_code == 201:
                print(f"Fee created successfully")
                return True
            else:
                print(f"Failed to create fee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error creating fee: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def update_fee(self, fee_id, fee_data):
        """Update existing fee"""
        endpoint = f"{self.url}/rest/v1/fees"
        params = {'id': f'eq.{fee_id}'}
        
        try:
            print(f"Updating fee {fee_id}: {fee_data}")
            response = requests.patch(endpoint, headers=self.headers, params=params, json=fee_data)
            
            if response.status_code in [200, 204]:
                print(f"Fee updated successfully")
                return True
            else:
                print(f"Failed to update fee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error updating fee: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_fee(self, fee_id):
        """Delete a fee"""
        endpoint = f"{self.url}/rest/v1/fees"
        params = {'id': f'eq.{fee_id}'}
        
        try:
            response = requests.delete(endpoint, headers=self.headers, params=params)
            
            if response.status_code in [200, 204]:
                print(f"Fee {fee_id} deleted successfully")
                return True
            else:
                print(f"Delete failed - Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            print(f"Error deleting fee: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ARCHIVED

    def get_archived_items(self):
        """Get all archived billing items"""
        try:
            endpoint = f"{self.url}/rest/v1/billing_items"
            params = {
                'status': 'eq.archived',
                'order': 'archived_at.desc'
            }
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error fetching archived items: {str(e)}")
            return []

    def archive_item(self, item_id, archived_by):
        """Archive a billing item"""
        try:
            endpoint = f"{self.url}/rest/v1/billing_items"
            params = {'id': f'eq.{item_id}'}
            
            from datetime import datetime
            update_data = {
                'status': 'archived',
                'archived_at': datetime.now().isoformat(),
                'archived_by': archived_by
            }
            
            response = requests.patch(
                endpoint,
                headers=self.headers,
                params=params,
                json=update_data
            )
            
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error archiving item: {str(e)}")
            return False

    def restore_from_archive(self, item_id):
        """Restore an archived item back to in_progress"""
        try:
            endpoint = f"{self.url}/rest/v1/billing_items"
            params = {'id': f'eq.{item_id}'}
            
            update_data = {
                'status': 'in_progress',
                'archived_at': None,
                'archived_by': None
            }
            
            response = requests.patch(
                endpoint,
                headers=self.headers,
                params=params,
                json=update_data
            )
            
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error restoring item: {str(e)}")
            return False

    def auto_archive_old_forms(self, days=30):
        """Auto-archive forms older than specified days"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            endpoint = f"{self.url}/rest/v1/billing_items"
            
            # Get items older than cutoff_date that are not already archived
            params = {
                'date': f'lt.{cutoff_date}',
                'status': 'neq.archived',
                'select': 'id,name,student_no,date'
            }
            
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                old_items = response.json()
                archived_count = 0
                
                for item in old_items:
                    if self.archive_item(item['id'], 'system_auto_archive'):
                        archived_count += 1
                
                return {
                    'success': True,
                    'archived_count': archived_count,
                    'total_found': len(old_items)
                }
            
            return {'success': False, 'archived_count': 0}
        
        except Exception as e:
            print(f"Error in auto-archive: {str(e)}")
            return {'success': False, 'error': str(e)}

    def delete_archived_item(self, item_id):
        """Permanently delete an archived item"""
        try:
            endpoint = f"{self.url}/rest/v1/billing_items"
            params = {'id': f'eq.{item_id}'}
            
            response = requests.delete(
                endpoint,
                headers=self.headers,
                params=params
            )
            
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error deleting item: {str(e)}")
            return False



# Create a singleton instance
supabase_client = SupabaseClient()