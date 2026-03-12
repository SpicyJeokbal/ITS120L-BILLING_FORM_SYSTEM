// frontend/static/js/fees.js

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

const csrftoken = getCookie('csrftoken');

// =================== MODAL FUNCTIONS ===================
function openModal() {
    document.getElementById('feeModal').classList.add('active');
}

function closeModal() {
    document.getElementById('feeModal').classList.remove('active');
    document.getElementById('feeForm').reset();
    document.getElementById('feeId').value = '';
    document.getElementById('feeModalTitle').textContent = 'Add Fee';
}

// Close modal on background click
document.getElementById('feeModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});

// =================== ADD FEE ===================
document.getElementById('addFeeBtn').addEventListener('click', function() {
    document.getElementById('feeModalTitle').textContent = 'Add Fee';
    document.getElementById('feeId').value = '';
    document.getElementById('feeForm').reset();
    openModal();
});

// =================== EDIT FEE ===================
function editFee(id, name, description, amount) {
    document.getElementById('feeModalTitle').textContent = 'Edit Fee';
    document.getElementById('feeId').value = id;
    document.getElementById('feeName').value = name;
    document.getElementById('feeDescription').value = description || '';
    document.getElementById('feeAmount').value = amount;
    openModal();
}

// =================== FORM SUBMISSION ===================
document.getElementById('feeForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('feeSubmitBtn');
    const feeId = document.getElementById('feeId').value;
    const isEdit = !!feeId;

    // Get form data
    const data = {
        name: document.getElementById('feeName').value.trim(),
        description: document.getElementById('feeDescription').value.trim(),
        amount: parseFloat(document.getElementById('feeAmount').value)
    };

    // Validation
    if (!data.name) {
        alert('Please enter a fee name');
        return;
    }

    if (!data.amount || data.amount < 0) {
        alert('Please enter a valid amount');
        return;
    }

    if (isEdit) {
        data.id = feeId;
    }

    // Disable submit button
    submitBtn.disabled = true;
    submitBtn.textContent = isEdit ? 'Updating...' : 'Adding...';

    try {
        const response = await fetch(isEdit ? '/fees/update/' : '/fees/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert(`Fee ${isEdit ? 'updated' : 'added'} successfully!`);
            location.reload();
        } else {
            alert('' + (result.message || 'Error saving fee'));
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Fee';
        }
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Fee';
    }
});

// =================== DELETE FEE ===================
function deleteFee(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
        return;
    }

    fetch('/fees/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ id: id })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Fee deleted successfully!');
            location.reload();
        } else {
            alert('' + (result.message || 'Error deleting fee'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred');
    });
}

// =================== SEARCH ===================
document.getElementById('searchInput').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('#feesTableBody tr[data-fee-id]');

    rows.forEach(row => {
        const name = row.cells[0]?.textContent.toLowerCase() || '';
        const description = row.cells[1]?.textContent.toLowerCase() || '';
        
        if (name.includes(searchTerm) || description.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});

// =================== UPDATE STATS ===================
function updateStats() {
    const rows = document.querySelectorAll('#feesTableBody tr[data-fee-id]');
    const amounts = [];

    rows.forEach(row => {
        const amountText = row.cells[2]?.textContent.replace('₱', '').replace(',', '') || '0';
        const amount = parseFloat(amountText);
        if (!isNaN(amount)) {
            amounts.push(amount);
        }
    });

    // Update total count
    document.getElementById('totalFees').textContent = amounts.length;

    if (amounts.length > 0) {
        // Calculate average
        const avg = amounts.reduce((sum, val) => sum + val, 0) / amounts.length;
        document.getElementById('avgFee').textContent = `₱${avg.toFixed(2)}`;

        // Calculate range
        const min = Math.min(...amounts);
        const max = Math.max(...amounts);
        document.getElementById('priceRange').textContent = `₱${min.toFixed(2)} - ₱${max.toFixed(2)}`;
    } else {
        document.getElementById('avgFee').textContent = '₱0.00';
        document.getElementById('priceRange').textContent = '₱0 - ₱0';
    }
}

// Initialize stats on page load
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
});

console.log('Fees page loaded');