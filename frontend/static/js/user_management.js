// frontend/static/js/user_management.js

// CSRF Token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Modal Functions
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Create User
document.getElementById('createUserBtn').addEventListener('click', function() {
    document.getElementById('createUserForm').reset();
    openModal('createUserModal');
});

document.getElementById('createUserForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const data = {
        username: document.getElementById('newUsername').value,
        full_name: document.getElementById('newFullName').value,
        email: document.getElementById('newEmail').value,
        password: document.getElementById('newPassword').value,
        role: document.getElementById('newRole').value
    };
    
    try {
        const response = await fetch('/user-management/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('User created successfully!');
            location.reload();
        } else {
            alert(result.message || 'Error creating user');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred');
    }
});

// Edit User
function editUser(username, currentRole, currentStatus) {
    document.getElementById('editUsername').value = username;
    document.getElementById('editRole').value = currentRole;
    document.getElementById('editStatus').value = currentStatus;
    openModal('editUserModal');
}

document.getElementById('editUserForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('editUsername').value;
    const role = document.getElementById('editRole').value;
    const status = document.getElementById('editStatus').value;
    
    try {
        // Update role
        const roleResponse = await fetch('/user-management/update-role/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ username, role })
        });
        
        // Update status
        const statusResponse = await fetch('/user-management/update-status/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ username, status })
        });
        
        const roleResult = await roleResponse.json();
        const statusResult = await statusResponse.json();
        
        if (roleResult.success && statusResult.success) {
            alert('User updated successfully!');
            location.reload();
        } else {
            alert('Error updating user');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred');
    }
});

// Reset Password
function resetPassword(username) {
    document.getElementById('resetUsername').value = username;
    document.getElementById('resetPasswordForm').reset();
    openModal('resetPasswordModal');
}

document.getElementById('resetPasswordForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const username = document.getElementById('resetUsername').value;
    const newPassword = document.getElementById('resetNewPassword').value;
    const confirmPassword = document.getElementById('resetConfirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        alert('Passwords do not match!');
        return;
    }
    
    if (newPassword.length < 8) {
        alert('Password must be at least 8 characters!');
        return;
    }
    
    try {
        const response = await fetch('/user-management/reset-password/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ username, new_password: newPassword })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('Password reset successfully!');
            closeModal('resetPasswordModal');
        } else {
            alert(result.message || 'Error resetting password');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred');
    }
});

// Delete User
function deleteUser(username) {
    if (!confirm(`Are you sure you want to delete user "${username}"? This action cannot be undone!`)) {
        return;
    }
    
    fetch('/user-management/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ username })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('User deleted successfully!');
            location.reload();
        } else {
            alert(result.message || 'Error deleting user');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
    });
}

// Close modal on background click
document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal(this.id);
        }
    });
}); 