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
        response = requests.delete(endpoint, headers=self.headers, params=params)
        return response.status_code == 204
    
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


# Create a singleton instance
supabase_client = SupabaseClient()