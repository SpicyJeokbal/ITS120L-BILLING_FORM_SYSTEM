// frontend/static/js/logs.js

let allLogs = [];
let filteredLogs = [];

// Load logs on page load
document.addEventListener('DOMContentLoaded', function() {
    loadLogs();
    
    // Auto-refresh every 30 seconds
    setInterval(loadLogs, 30000);
    
    // Event listeners
    document.getElementById('refreshBtn').addEventListener('click', loadLogs);
    document.getElementById('exportBtn').addEventListener('click', exportLogs);
    document.getElementById('searchInput').addEventListener('input', filterLogs);
    document.getElementById('activityFilter').addEventListener('change', filterLogs);
    document.getElementById('dateFilter').addEventListener('change', filterLogs);
});

async function loadLogs() {
    try {
        //const response = await fetch('/logs/api/');
        const response = await fetch('/logs/api/', {
            credentials: 'same-origin'
        });
        const data = await response.json();
        
        if (data.success) {
            allLogs = data.logs;
            filteredLogs = allLogs;
            renderLogs();
            updateStats();
        } else {
            showError('Failed to load logs');
        }
    } catch (error) {
        console.error('Error loading logs:', error);
        showError('Error loading logs');
    }
}

function renderLogs() {
    const tbody = document.getElementById('logsTableBody');
    const logCount = document.getElementById('logCount');
    
    logCount.textContent = `Showing ${filteredLogs.length} logs`;
    
    if (filteredLogs.length === 0) {
        tbody.innerHTML = `
            <tr class="empty-state">
                <td colspan="5">
                    <svg fill="currentColor" viewBox="0 0 16 16">
                        <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                        <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                    </svg>
                    <p>No logs found</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = filteredLogs.map(log => `
        <tr>
            <td>
                <div class="log-time">${formatTimestamp(log.timestamp)}</div>
            </td>
            <td>
                <div class="log-user">${escapeHtml(log.username)}</div>
            </td>
            <td>
                <span class="log-activity activity-${log.activity_type}">
                    ${formatActivityType(log.activity_type)}
                </span>
            </td>
            <td>
                <div class="log-details">${escapeHtml(log.details || '-')}</div>
            </td>
            <td>
                <div class="log-ip">${escapeHtml(log.ip_address || 'N/A')}</div>
            </td>
        </tr>
    `).join('');
}

function filterLogs() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const activityType = document.getElementById('activityFilter').value;
    const dateFilter = document.getElementById('dateFilter').value;
    
    filteredLogs = allLogs.filter(log => {
        // Search filter
        const matchesSearch = searchTerm === '' || 
            log.username.toLowerCase().includes(searchTerm) ||
            log.activity_type.toLowerCase().includes(searchTerm) ||
            (log.details && log.details.toLowerCase().includes(searchTerm));
        
        // Activity type filter
        const matchesActivity = activityType === '' || log.activity_type === activityType;
        
        // Date filter
        const matchesDate = dateFilter === '' || log.timestamp.startsWith(dateFilter);
        
        return matchesSearch && matchesActivity && matchesDate;
    });
    
    renderLogs();
}

function updateStats() {
    const today = new Date().toISOString().split('T')[0];
    
    // Count logins today
    const loginsToday = allLogs.filter(log => 
        log.activity_type === 'login' && log.timestamp.startsWith(today)
    ).length;
    
    // Count all activities today
    const activitiesToday = allLogs.filter(log => 
        log.timestamp.startsWith(today)
    ).length;
    
    // Count unique users
    const uniqueUsers = new Set(allLogs.map(log => log.username)).size;
    
    document.getElementById('totalLogins').textContent = loginsToday;
    document.getElementById('totalActivities').textContent = activitiesToday;
    document.getElementById('activeUsers').textContent = uniqueUsers;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatActivityType(type) {
    const formats = {
        'login': 'Login',
        'logout': 'Logout',
        'create_billing': 'Create',
        'update_billing': 'Update',
        'delete_billing': 'Delete'
    };
    return formats[type] || type;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function exportLogs() {
    // Create CSV content
    const headers = ['Timestamp', 'User', 'Activity', 'Details', 'IP Address'];
    const csvContent = [
        headers.join(','),
        ...filteredLogs.map(log => [
            log.timestamp,
            log.username,
            log.activity_type,
            log.details || '',
            log.ip_address || ''
        ].map(field => `"${field}"`).join(','))
    ].join('\n');
    
    // Download CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `activity-logs-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function showError(message) {
    const tbody = document.getElementById('logsTableBody');
    tbody.innerHTML = `
        <tr>
            <td colspan="5" style="text-align: center; padding: 40px; color: #e74c3c;">
                ${message}
            </td>
        </tr>
    `;
}