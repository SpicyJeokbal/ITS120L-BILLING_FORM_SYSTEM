// frontend/static/js/main.js

let draggedCard = null;

// =================== SEARCH FUNCTIONALITY ===================
document.getElementById('searchInput').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    document.querySelectorAll('.card').forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
});

// =================== DRAG AND DROP ===================
document.querySelectorAll('.card').forEach(card => {
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    card.addEventListener('dblclick', handleCardDoubleClick);
});

document.querySelectorAll('.drop-zone').forEach(zone => {
    zone.addEventListener('dragover', handleDragOver);
    zone.addEventListener('drop', handleDrop);
    zone.addEventListener('dragleave', handleDragLeave);
});

function handleCardDoubleClick(e) {
    const itemId = this.dataset.id;
    console.log('Double-clicked card ID:', itemId);
    openBillingView(itemId);
}

function handleDragStart(e) {
    draggedCard = this;
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragEnd(e) {
    this.classList.remove('dragging');
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('drag-over');
    return false;
}

function handleDragLeave(e) {
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    this.classList.remove('drag-over');
    
    if (draggedCard) {
        const newStatus = this.dataset.status;
        const itemId = draggedCard.dataset.id;
        
        this.appendChild(draggedCard);
        updateCounts();
        updateItemStatus(itemId, newStatus);
    }
    
    return false;
}

function updateCounts() {
    document.querySelectorAll('.column').forEach(column => {
        const count = column.querySelectorAll('.card').length;
        column.querySelector('.column-count').textContent = count;
    });
}

function updateItemStatus(itemId, status) {
    fetch('/update-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            item_id: itemId,
            status: status
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Error updating status');
            location.reload();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error updating status');
        location.reload();
    });
}

// =================== MODAL FUNCTIONALITY ===================
const modal = document.getElementById('addItemModal');
const addButtons = document.querySelectorAll('.add-card-btn');
const closeModal = document.getElementById('closeModal');
const addItemForm = document.getElementById('addItemForm');

// Open modal when clicking + button
addButtons.forEach(button => {
    button.addEventListener('click', function(e) {
        e.preventDefault();
        const status = this.dataset.status;
        document.getElementById('item_status').value = status;
        modal.classList.add('active');
        setCurrentDate();
        generateChargeNumber();
    });
});

// Close modal functions
function closeModalFunc() {
    modal.classList.remove('active');
    addItemForm.reset();
    // Reset to single item
    const descriptionItems = document.getElementById('descriptionItems');
    descriptionItems.innerHTML = `
        <div class="description-item">
            <input type="text" class="form-input description-input" placeholder="PRINTING - BLCK GRAPHICS" value="PRINTING - BLCK GRAPHICS">
            <div class="quantity-controls">
                <button type="button" class="qty-btn qty-minus">−</button>
                <input type="number" class="qty-input" value="1" min="1">
                <button type="button" class="qty-btn qty-plus">+</button>
            </div>
            <input type="number" class="form-input amount-input" placeholder="₱5" value="5" step="0.01">
            <button type="button" class="btn-remove-item">×</button>
        </div>
    `;
    attachDescriptionItemEvents();
    updateSummary();
}

closeModal.addEventListener('click', closeModalFunc);

// Close modal when clicking outside
modal.addEventListener('click', function(e) {
    if (e.target === modal) {
        closeModalFunc();
    }
});

// =================== DYNAMIC DESCRIPTION ITEMS ===================
function attachDescriptionItemEvents() {
    // Quantity buttons
    document.querySelectorAll('.qty-minus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.qty-input');
            if (input.value > 1) {
                input.value = parseInt(input.value) - 1;
                updateSummary();
            }
        });
    });

    document.querySelectorAll('.qty-plus').forEach(btn => {
        btn.addEventListener('click', function() {
            const input = this.parentElement.querySelector('.qty-input');
            input.value = parseInt(input.value) + 1;
            updateSummary();
        });
    });

    // Quantity input change
    document.querySelectorAll('.qty-input').forEach(input => {
        input.addEventListener('input', updateSummary);
    });

    // Amount input change
    document.querySelectorAll('.amount-input').forEach(input => {
        input.addEventListener('input', updateSummary);
    });

    // Description input change
    document.querySelectorAll('.description-input').forEach(input => {
        input.addEventListener('input', updateSummary);
    });

    // Remove item buttons
    document.querySelectorAll('.btn-remove-item').forEach(btn => {
        btn.addEventListener('click', function() {
            const items = document.querySelectorAll('.description-item');
            if (items.length > 1) {
                this.closest('.description-item').remove();
                updateSummary();
            } else {
                alert('You must have at least one item');
            }
        });
    });
}

// Add new description item
document.getElementById('addDescriptionItem').addEventListener('click', function() {
    const descriptionItems = document.getElementById('descriptionItems');
    const newItem = document.createElement('div');
    newItem.className = 'description-item';
    newItem.innerHTML = `
        <input type="text" class="form-input description-input" placeholder="Item description">
        <div class="quantity-controls">
            <button type="button" class="qty-btn qty-minus">−</button>
            <input type="number" class="qty-input" value="1" min="1">
            <button type="button" class="qty-btn qty-plus">+</button>
        </div>
        <input type="number" class="form-input amount-input" placeholder="₱0" value="0" step="0.01">
        <button type="button" class="btn-remove-item">×</button>
    `;
    descriptionItems.appendChild(newItem);
    attachDescriptionItemEvents();
    updateSummary();
});

// Initial event attachment
attachDescriptionItemEvents();

// =================== SUMMARY CALCULATION ===================
function updateSummary() {
    const items = document.querySelectorAll('.description-item');
    const breakdownDiv = document.getElementById('amountBreakdown');
    const totalDiv = document.getElementById('totalAmount');
    
    let total = 0;
    let breakdownHTML = '';
    
    items.forEach(item => {
        const description = item.querySelector('.description-input').value || 'Item';
        const quantity = parseInt(item.querySelector('.qty-input').value) || 0;
        const amount = parseFloat(item.querySelector('.amount-input').value) || 0;
        const itemTotal = quantity * amount;
        
        total += itemTotal;
        
        if (description && quantity > 0 && amount > 0) {
            breakdownHTML += `
                <div class="amount-item">
                    <span>${description}(${quantity})</span>
                    <span>₱${itemTotal.toFixed(2)}</span>
                </div>
            `;
        }
    });
    
    breakdownDiv.innerHTML = breakdownHTML || '<div class="amount-item"><span>No items</span><span>₱0.00</span></div>';
    totalDiv.textContent = `₱${total.toFixed(2)}`;
}

// =================== HELPER FUNCTIONS ===================
function setCurrentDate() {
    const today = new Date();
    
    // Format for display: MM/DD/YYYY
    const displayFormatted = today.toLocaleDateString('en-US', { 
        month: '2-digit', 
        day: '2-digit', 
        year: 'numeric' 
    });
    document.getElementById('chargeDate').textContent = displayFormatted;
    
    // Format for database: YYYY-MM-DD
    const dbFormatted = today.toISOString().split('T')[0];
    document.getElementById('chargeDate').setAttribute('data-db-date', dbFormatted);
}

function generateChargeNumber() {
    // In a real application, this would come from the backend
    const random = Math.floor(Math.random() * 999999) + 1;
    document.getElementById('chargeNumber').textContent = String(random).padStart(6, '0');
}

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

// =================== FORM SUBMISSION ===================
addItemForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    console.log('=== FORM SUBMISSION DEBUG ===');
    
    // Collect all description items
    const items = [];
    document.querySelectorAll('.description-item').forEach(item => {
        const description = item.querySelector('.description-input').value;
        const quantity = parseInt(item.querySelector('.qty-input').value);
        const amount = parseFloat(item.querySelector('.amount-input').value);
        
        if (description && quantity > 0 && amount > 0) {
            items.push({
                description: description,
                quantity: quantity,
                amount: amount
            });
        }
    });
    
    console.log('Items collected:', items);
    
    if (items.length === 0) {
        alert('Please add at least one item with description, quantity, and amount');
        return;
    }
    
    // Calculate total
    const total = items.reduce((sum, item) => sum + (item.quantity * item.amount), 0);
    
    // Get the database-formatted date (YYYY-MM-DD)
    const dbDate = document.getElementById('chargeDate').getAttribute('data-db-date');
    
    const formData = {
        name: document.getElementById('student_name').value,
        student_no: document.getElementById('student_no').value,
        program: document.getElementById('program').value,
        term: document.getElementById('term').value,
        academic_year: document.getElementById('academic_year').value || '2025-2026',
        items: items,
        total: total,
        charged_by: document.getElementById('charged_by').value,
        status: document.getElementById('item_status').value,
        charge_number: document.getElementById('chargeNumber').textContent,
        date: dbDate  // Use YYYY-MM-DD format for database
    };
    
    console.log('Form data to submit:', formData);
    
    // Disable submit button
    const submitBtn = this.querySelector('.btn-save');
    submitBtn.disabled = true;
    submitBtn.textContent = 'SAVING...';
    
    // Send to backend
    fetch('/create-billing/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json().then(data => ({
            status: response.status,
            data: data
        }));
    })
    .then(result => {
        console.log('Response data:', result.data);
        
        if (result.status === 200 && result.data.success) {
            alert('Billing form created successfully!');
            location.reload();
        } else {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'SAVE';
            
            const errorMsg = result.data.message || 'Unknown error occurred';
            alert('Error creating billing form: ' + errorMsg);
            console.error('Server error:', result.data);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.textContent = 'SAVE';
        
        alert('Error creating billing form. Please check the console for details.');
    });
});

// Initialize summary on page load
updateSummary();

// =================== VIEW BILLING DETAILS ===================
function openBillingView(itemId) {
    console.log('Fetching billing details for ID:', itemId);
    
    // Fetch billing details from backend
    fetch(`/get-billing/${itemId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayBillingModal(data.item);
        } else {
            alert('Error loading billing details: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error fetching billing details:', error);
        alert('Error loading billing details');
    });
}

function displayBillingModal(item) {
    console.log('Displaying item:', item);
    
    // Populate the modal with item data
    document.getElementById('student_name').value = item.name || '';
    document.getElementById('student_no').value = item.student_no || '';
    document.getElementById('program').value = item.program_year || '';
    document.getElementById('term').value = item.term || '';
    document.getElementById('academic_year').value = item.school_year || '';
    
    // Clear existing items
    const descriptionItems = document.getElementById('descriptionItems');
    descriptionItems.innerHTML = '';
    
    // Parse and display items
    // The description is stored as comma-separated items like "PRINTING - BLCK GRAPHICS (x5), Lost Book (x1)"
    const descriptionParts = item.description.split(',');
    
    descriptionParts.forEach(part => {
        const trimmed = part.trim();
        // Extract description and quantity using regex
        const match = trimmed.match(/^(.+?)\s*\(x(\d+)\)$/);
        
        if (match) {
            const description = match[1].trim();
            const quantity = parseInt(match[2]);
            const amount = item.amount || 0; // You might want to store individual amounts
            
            addDescriptionItemToModal(description, quantity, amount);
        } else {
            // Fallback if format doesn't match
            addDescriptionItemToModal(trimmed, 1, item.amount || 0);
        }
    });
    
    // Update summary
    document.getElementById('chargeNumber').textContent = item.id.toString().padStart(6, '0');
    document.getElementById('chargeDate').textContent = formatDate(item.date);
    document.getElementById('chargeDate').setAttribute('data-db-date', item.date);
    
    // Update charged by
    document.getElementById('charged_by').value = item.charged_by || '';
    const chargedByDisplay = document.querySelector('.charged-by-name');
    if (chargedByDisplay) {
        chargedByDisplay.textContent = (item.charged_by || '').toUpperCase();
    }
    
    // Set the status
    document.getElementById('item_status').value = item.status || 'in_progress';
    
    // Update the summary
    updateSummary();
    
    // Make form read-only
    makeFormReadOnly(true);
    
    // Change button to "Close" instead of "Save"
    const submitBtn = document.querySelector('.btn-save');
    submitBtn.textContent = 'CLOSE';
    submitBtn.type = 'button';
    submitBtn.onclick = function() {
        closeModalFunc();
        // Reset form back to editable mode
        makeFormReadOnly(false);
        submitBtn.textContent = 'SAVE';
        submitBtn.type = 'submit';
        submitBtn.onclick = null;
    };
    
    // Open the modal
    modal.classList.add('active');
}

function addDescriptionItemToModal(description, quantity, amount) {
    const descriptionItems = document.getElementById('descriptionItems');
    const newItem = document.createElement('div');
    newItem.className = 'description-item';
    newItem.innerHTML = `
        <input type="text" class="form-input description-input" value="${description}">
        <div class="quantity-controls">
            <button type="button" class="qty-btn qty-minus">−</button>
            <input type="number" class="qty-input" value="${quantity}" min="1">
            <button type="button" class="qty-btn qty-plus">+</button>
        </div>
        <input type="number" class="form-input amount-input" value="${amount}" step="0.01">
        <button type="button" class="btn-remove-item">×</button>
    `;
    descriptionItems.appendChild(newItem);
    attachDescriptionItemEvents();
}

function makeFormReadOnly(readonly) {
    const formInputs = document.querySelectorAll('#addItemForm input, #addItemForm select, #addItemForm textarea');
    const buttons = document.querySelectorAll('.qty-btn, .btn-remove-item, #addDescriptionItem');
    
    formInputs.forEach(input => {
        if (readonly) {
            input.setAttribute('readonly', 'readonly');
            input.setAttribute('disabled', 'disabled');
        } else {
            input.removeAttribute('readonly');
            input.removeAttribute('disabled');
        }
    });
    
    buttons.forEach(btn => {
        if (readonly) {
            btn.style.display = 'none';
        } else {
            btn.style.display = '';
        }
    });
}

function formatDate(dateString) {
    // Convert YYYY-MM-DD to MM/DD/YYYY
    const parts = dateString.split('-');
    if (parts.length === 3) {
        return `${parts[1]}/${parts[2]}/${parts[0]}`;
    }
    return dateString;
}