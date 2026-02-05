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
    
    def log_user_activity(self, username, activity_type):
        """Log user activity (login/logout) in Supabase"""
        endpoint = f"{self.url}/rest/v1/user_activity_logs"
        data = {
            'username': username,
            'activity_type': activity_type,
            'timestamp': datetime.now().isoformat()
        }
        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            return response.status_code == 201
        except Exception as e:
            print(f"Error logging activity: {e}")
            return False

# Create a singleton instance
supabase_client = SupabaseClient()