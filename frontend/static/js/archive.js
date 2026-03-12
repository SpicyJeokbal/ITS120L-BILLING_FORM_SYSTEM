// frontend/static/js/archive.js

// Search functionality
document.getElementById('searchInput')?.addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    document.querySelectorAll('.archive-card').forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
});

// Toggle archive menu
function toggleArchiveMenu(event, itemId) {
    event.stopPropagation();
    
    const dropdown = document.getElementById(`archiveMenu${itemId}`);
    const allDropdowns = document.querySelectorAll('.archive-menu-dropdown');
    
    allDropdowns.forEach(d => {
        if (d !== dropdown) {
            d.classList.remove('active');
        }
    });
    
    dropdown.classList.toggle('active');
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.archive-card-menu')) {
        document.querySelectorAll('.archive-menu-dropdown').forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    }
});

// View archived form details
function viewArchivedForm(itemId) {
    window.location.href = `/get-billing/${itemId}/`;
}

// Restore form from archive
function restoreForm(itemId) {
    if (!confirm('Restore this form back to In Progress?')) {
        return;
    }
    
    fetch('/archive/restore/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Form restored successfully!');
            location.reload();
        } else {
            alert('❌ Error: ' + (data.message || 'Failed to restore form'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ An error occurred');
    });
}

// Permanently delete form
function permanentlyDeleteForm(itemId) {
    if (!confirm('⚠️ PERMANENTLY DELETE this form? This action cannot be undone!')) {
        return;
    }
    
    if (!confirm('Are you absolutely sure? This will permanently delete all data.')) {
        return;
    }
    
    fetch('/archive/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ item_id: itemId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Form permanently deleted');
            location.reload();
        } else {
            alert('❌ Error: ' + (data.message || 'Failed to delete form'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ An error occurred');
    });
}

// Run auto-archive
function runAutoArchive() {
    if (!confirm('Auto-archive all forms older than 30 days?')) {
        return;
    }
    
    const btn = event.target.closest('.btn-auto-archive');
    btn.disabled = true;
    btn.textContent = 'Processing...';
    
    fetch('/archive/auto-run/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`✅ Successfully archived ${data.archived_count} forms (found ${data.total_found} eligible)`);
            location.reload();
        } else {
            alert('❌ Error: ' + (data.message || 'Auto-archive failed'));
            btn.disabled = false;
            btn.textContent = 'Auto-Archive Old Forms';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('❌ An error occurred');
        btn.disabled = false;
        btn.textContent = 'Auto-Archive Old Forms';
    });
}

// Get CSRF token
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

console.log('✅ Archive script loaded');