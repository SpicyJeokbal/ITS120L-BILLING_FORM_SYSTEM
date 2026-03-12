// frontend/static/js/main.js

let draggedCard = null;

// =================== HELPER FUNCTIONS ===================
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

function setCurrentDate() {
    const today = new Date();
    
    const displayFormatted = today.toLocaleDateString('en-US', { 
        month: '2-digit', 
        day: '2-digit', 
        year: 'numeric' 
    });
    document.getElementById('chargeDate').textContent = displayFormatted;
    
    const dbFormatted = today.toISOString().split('T')[0];
    document.getElementById('chargeDate').setAttribute('data-db-date', dbFormatted);
}

function generateChargeNumber() {
    const random = Math.floor(Math.random() * 999999) + 1;
    document.getElementById('chargeNumber').textContent = String(random).padStart(6, '0');
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function formatDate(dateString) {
    const parts = dateString.split('-');
    if (parts.length === 3) {
        return `${parts[1]}/${parts[2]}/${parts[0]}`;
    }
    return dateString;
}

// =================== CARD MENU DROPDOWN ===================

function toggleCardMenu(event, itemId) {
    event.stopPropagation();
    const dropdown = document.getElementById(`cardMenu${itemId}`);
    const allDropdowns = document.querySelectorAll('.card-menu-dropdown');
    allDropdowns.forEach(d => {
        if (d !== dropdown) {
            d.classList.remove('active');
        }
    });
    dropdown.classList.toggle('active');
}

function downloadForm(itemId) {
    console.log('Download form:', itemId);
    fetch(`/download-form/${itemId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `billing_form_${itemId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    })
    .catch(error => {
        console.error('Download error:', error);
        alert('Download feature coming soon!');
    });
}

function archiveForm(itemId) {
    console.log('Archive form:', itemId);
    if (!confirm('Archive this billing form?')) {
        return;
    }
    fetch('/archive/form/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            item_id: itemId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Form archived successfully!');
            location.reload();
        } else {
            alert('❌ Error: ' + (data.message || 'Failed to archive form'));
        }
    })
    .catch(error => {
        console.error('Archive error:', error);
        alert('❌ An error occurred');
    });
}

function deleteForm(itemId) {
    if (!confirm('Are you sure you want to permanently delete this billing form? This action cannot be undone!')) {
        return;
    }
    
    console.log('Delete form:', itemId);
    
    fetch(`/delete-billing/${itemId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),  
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Billing form deleted successfully!');
            location.reload();
        } else {
            alert('Error: ' + (data.message || 'Failed to delete form'));
        }
    })
    .catch(error => {
        console.error('Delete error:', error);
        alert('An error occurred while deleting the form');
    });
}

// =================== REPORTS DROPDOWN ===================

function toggleReportsDropdown() {
    const btn = document.getElementById('reportsDropdownBtn');
    const menu = document.getElementById('reportsDropdownMenu');
    
    btn.classList.toggle('active');
    menu.classList.toggle('active');
}

function exportToExcel() {
    console.log('Exporting to Excel...');
    const btn = event.target.closest('.reports-dropdown-item');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Generating...</span>';
    
    fetch('/export/excel/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `billing_forms_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('✅ Excel exported successfully!');
        toggleReportsDropdown();
    })
    .catch(error => {
        console.error('Export error:', error);
        alert('❌ Export failed. Please try again.');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = `
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                <path d="M5.884 6.68a.5.5 0 1 0-.768.64L7.349 10l-2.233 2.68a.5.5 0 0 0 .768.64L8 10.781l2.116 2.54a.5.5 0 0 0 .768-.641L8.651 10l2.233-2.68a.5.5 0 0 0-.768-.64L8 9.219l-2.116-2.54z"/>
            </svg>
            <div class="reports-item-content">
                <div class="reports-item-title">Export to Excel</div>
                <div class="reports-item-subtitle">All forms including archived</div>
            </div>
        `;
    });
}

function exportToPDF() {
    console.log('Exporting to PDF...');
    const btn = event.target.closest('.reports-dropdown-item');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Generating...</span>';
    
    fetch('/export/pdf/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('Export failed');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `billing_report_${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('✅ PDF exported successfully!');
        toggleReportsDropdown();
    })
    .catch(error => {
        console.error('Export error:', error);
        alert('❌ Export failed. Please try again.');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = `
            <svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 0 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                <path fill-rule="evenodd" d="M4.603 14.087a.81.81 0 0 1-.438-.42c-.195-.388-.13-.776.08-1.102.198-.307.526-.568.897-.787a7.68 7.68 0 0 1 1.482-.645 19.697 19.697 0 0 0 1.062-2.227 7.269 7.269 0 0 1-.43-1.295c-.086-.4-.119-.796-.046-1.136.075-.354.274-.672.65-.823.192-.077.4-.12.602-.077a.7.7 0 0 1 .477.365c.088.164.12.356.127.538.007.188-.012.396-.047.614-.084.51-.27 1.134-.52 1.794a10.954 10.954 0 0 0 .98 1.686 5.753 5.753 0 0 1 1.334.05c.364.066.734.195.96.465.12.144.193.32.2.518.007.192-.047.382-.138.563a1.04 1.04 0 0 1-.354.416.856.856 0 0 1-.51.138c-.331-.014-.654-.196-.933-.417a5.712 5.712 0 0 1-.911-.95 11.651 11.651 0 0 0-1.997.406 11.307 11.307 0 0 1-1.02 1.51c-.292.35-.609.656-.927.787a.793.793 0 0 1-.58.029zm1.379-1.901c-.166.076-.32.156-.459.238-.328.194-.541.383-.647.547-.094.145-.096.25-.04.361.01.022.02.036.026.044a.266.266 0 0 0 .035-.012c.137-.056.355-.235.635-.572a8.18 8.18 0 0 0 .45-.606zm1.64-1.33a12.71 12.71 0 0 1 1.01-.193 11.744 11.744 0 0 1-.51-.858 20.801 20.801 0 0 1-.5 1.05zm2.446.45c.15.163.296.3.435.41.24.19.407.253.498.256a.107.107 0 0 0 .07-.015.307.307 0 0 0 .094-.125.436.436 0 0 0 .059-.2.095.095 0 0 0-.026-.063c-.052-.062-.2-.152-.518-.209a3.876 3.876 0 0 0-.612-.053zM8.078 7.8a6.7 6.7 0 0 0 .2-.828c.031-.188.043-.343.038-.465a.613.613 0 0 0-.032-.198.517.517 0 0 0-.145.04c-.087.035-.158.106-.196.283-.04.192-.03.469.046.822.024.111.054.227.09.346z"/>
            </svg>
            <div class="reports-item-content">
                <div class="reports-item-title">Export to PDF</div>
                <div class="reports-item-subtitle">Summary report with all forms</div>
            </div>
        `;
    });
}

// =================== BILLING VIEW FUNCTIONS ===================

function openBillingView(itemId) {
    console.log('Fetching billing details for ID:', itemId);
    
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
    const modal = document.getElementById('addItemModal');
    console.log('Displaying item:', item);
    
    document.getElementById('student_name').value = item.name || '';
    document.getElementById('student_no').value = item.student_no || '';
    document.getElementById('program').value = item.program_year || '';
    document.getElementById('term').value = item.term || '';
    document.getElementById('academic_year').value = item.school_year || '';
    
    selectedFeesMap.clear();
    
    const descriptionParts = item.description.split(',');
    descriptionParts.forEach((part, index) => {
        const trimmed = part.trim();
        const match = trimmed.match(/^(.+?)\s*\(x?(\d+)\)$/);
        
        if (match) {
            const description = match[1].trim();
            const quantity = parseInt(match[2]);
            
            selectedFeesMap.set(index, {
                fee: {
                    id: index,
                    name: description,
                    amount: item.amount || 0
                },
                quantity: quantity
            });
        }
    });
    
    renderSelectedFees();
    
    document.getElementById('chargeNumber').textContent = item.id.toString().padStart(6, '0');
    document.getElementById('chargeDate').textContent = formatDate(item.date);
    document.getElementById('chargeDate').setAttribute('data-db-date', item.date);
    
    document.getElementById('charged_by').value = item.charged_by || '';
    const chargedByDisplay = document.querySelector('.charged-by-name');
    if (chargedByDisplay) {
        chargedByDisplay.textContent = (item.charged_by || '').toUpperCase();
    }
    
    const librarianSection = document.querySelector('.signature-section .signature-group:first-child');
    if (librarianSection) {
        const existingDisplay = librarianSection.querySelector('.signature-display');
        if (existingDisplay) {
            existingDisplay.remove();
        }
        
        if (item.librarian_signature) {
            const placeholder = librarianSection.querySelector('.signature-placeholder');
            if (placeholder) {
                placeholder.style.display = 'none';
            }
            
            const signatureDisplay = document.createElement('div');
            signatureDisplay.className = 'signature-display';
            signatureDisplay.innerHTML = `
                <div class="librarian-signature-container">
                    <img src="${item.librarian_signature}" 
                         alt="Librarian Signature" 
                         class="librarian-signature-img">
                    <div class="librarian-name-below">${(item.charged_by || 'LIBRARIAN').toUpperCase()}</div>
                </div>
            `;
            
            const signatureLine = librarianSection.querySelector('.signature-line');
            if (signatureLine) {
                signatureLine.parentNode.insertBefore(signatureDisplay, signatureLine);
            }
        }
    }
    
    const conformeSection = document.querySelector('.signature-group:last-child');
    const signaturePlaceholder = conformeSection.querySelector('.signature-placeholder');
    
    if (item.student_signature) {
        signaturePlaceholder.innerHTML = `
            <div class="student-signature-display">
                <img src="${item.student_signature}" alt="Student Signature" class="signature-image">
                ${item.student_signed_at ? `<div class="signature-timestamp">Signed: ${formatDateTime(item.student_signed_at)}</div>` : ''}
            </div>
        `;
        
        if (item.status === 'awaiting_approval') {
            addAwaitingApprovalBadge();
        }
    } else {
        signaturePlaceholder.innerHTML = '<span class="no-signature-text">Awaiting student signature</span>';
    }
    
    document.getElementById('item_status').value = item.status || 'in_progress';
    
    updateSummary();
    makeFormReadOnly(true);
    updateModalButtons(item);
    modal.classList.add('active');
}

function makeFormReadOnly(readonly) {
    const formInputs = document.querySelectorAll('#addItemForm input, #addItemForm select, #addItemForm textarea');
    const buttons = document.querySelectorAll('#btnAddFeeItem');
    
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
    
    const qtyButtons = document.querySelectorAll('.selected-fee-qty button, .selected-fee-remove');
    qtyButtons.forEach(btn => {
        if (readonly) {
            btn.style.display = 'none';
        } else {
            btn.style.display = '';
        }
    });
}

function addAwaitingApprovalBadge() {
    const modalHeader = document.querySelector('.modal-header h2');
    
    const existingBadge = document.querySelector('.status-badge');
    if (existingBadge) {
        existingBadge.remove();
    }
    
    const badge = document.createElement('span');
    badge.className = 'status-badge status-awaiting';
    badge.textContent = 'Awaiting Approval';
    modalHeader.appendChild(badge);
}

function updateModalButtons(item) {
    const submitBtn = document.querySelector('.btn-save');
    const formRight = document.querySelector('.form-right');
    
    const existingActions = document.querySelector('.approval-actions');
    if (existingActions) {
        existingActions.remove();
    }
    
    if (item.status === 'awaiting_approval' && item.student_signature) {
        submitBtn.style.display = 'none';
        
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'approval-actions';
        actionsDiv.innerHTML = `
            <button type="button" class="btn-approve" onclick="approveForm(${item.id})">
                ✓ Approve & Move to In Progress
            </button>
            <button type="button" class="btn-reject" onclick="rejectForm(${item.id})">
                ✕ Reject
            </button>
            <button type="button" class="btn-close-modal" onclick="closeModalFunc()">
                Close
            </button>
        `;
        formRight.appendChild(actionsDiv);
    } else {
        submitBtn.textContent = 'CLOSE';
        submitBtn.type = 'button';
        submitBtn.style.display = 'block';
        submitBtn.onclick = function() {
            closeModalFunc();
            makeFormReadOnly(false);
            submitBtn.textContent = 'SAVE';
            submitBtn.type = 'submit';
            submitBtn.onclick = null;
        };
    }
}

function approveForm(itemId) {
    if (!confirm('Approve this billing form and move to In Progress?')) {
        return;
    }
    
    fetch('/update-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            item_id: itemId,
            status: 'in_progress'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Form approved successfully!');
            location.reload();
        } else {
            alert('Error approving form');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error approving form');
    });
}

function rejectForm(itemId) {
    const reason = prompt('Reason for rejection (optional):');
    
    if (reason === null) {
        return;
    }
    
    if (confirm('Are you sure you want to reject this form? This action cannot be undone.')) {
        alert('Rejection functionality coming soon. Form marked for review.');
        closeModalFunc();
    }
}

async function loadLibrarianSignature() {
    try {
        const response = await fetch('/signature-settings/get/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const result = await response.json();
        
        if (result.success && result.signature) {
            const signatureSection = document.querySelector('.signature-section .signature-group:first-child');
            
            if (signatureSection) {
                const placeholder = signatureSection.querySelector('.signature-placeholder');
                if (placeholder) {
                    placeholder.style.display = 'none';
                }
                
                let signatureDisplay = signatureSection.querySelector('.signature-display');
                
                if (!signatureDisplay) {
                    signatureDisplay = document.createElement('div');
                    signatureDisplay.className = 'signature-display';
                    
                    const signatureLine = signatureSection.querySelector('.signature-line');
                    
                    if (signatureLine) {
                        signatureLine.parentNode.insertBefore(signatureDisplay, signatureLine);
                    }
                }
                
                const chargedByName = document.getElementById('charged_by')?.value || 
                                      document.querySelector('.charged-by-name')?.textContent || 
                                      'Librarian';
                
                signatureDisplay.innerHTML = `
                    <div class="librarian-signature-container">
                        <img src="${result.signature}" 
                             alt="Librarian Signature" 
                             class="librarian-signature-img">
                        <div class="librarian-name-below">${chargedByName.toUpperCase()}</div>
                    </div>
                `;
                
                console.log('✅ Librarian signature loaded');
            }
        } else {
            console.log('ℹ️ No signature found');
        }
    } catch (error) {
        console.error('❌ Error loading signature:', error);
    }
}

// =================== FEE SELECTOR SYSTEM ===================
let availableFees = [];
let selectedFeesMap = new Map();
let tempSelectedFees = new Set();

async function loadAvailableFees() {
    try {
        console.log('🔄 Loading fees from database...');
        
        const response = await fetch('/fees/list/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const result = await response.json();
        
        if (result.success && result.fees) {
            availableFees = result.fees;
            console.log(`✅ Loaded ${availableFees.length} fees`);
        } else {
            availableFees = [];
            console.warn('⚠️ No fees found');
        }
    } catch (error) {
        console.error('❌ Error loading fees:', error);
        availableFees = [];
    }
}

function openFeeSelector() {
    const overlay = document.getElementById('feeSelectorOverlay');
    
    if (!overlay) {
        console.error('❌ Fee selector overlay not found!');
        return;
    }
    
    const searchInput = document.getElementById('feeSearchInput');
    if (searchInput) {
        searchInput.value = '';
    }
    
    tempSelectedFees.clear();
    selectedFeesMap.forEach((data, feeId) => {
        tempSelectedFees.add(feeId);
    });
    
    renderFeeOptions();
    overlay.classList.add('active');
}

function closeFeeSelector() {
    const overlay = document.getElementById('feeSelectorOverlay');
    if (overlay) {
        overlay.classList.remove('active');
    }
}

function renderFeeOptions(searchTerm = '') {
    const body = document.getElementById('feeSelectorBody');
    
    if (!body) {
        console.error('❌ Fee selector body not found!');
        return;
    }
    
    if (availableFees.length === 0) {
        body.innerHTML = `
            <div class="no-fees-message">
                <svg width="48" height="48" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M4 10.781c.148 1.667 1.513 2.85 3.591 3.003V15h1.043v-1.216c2.27-.179 3.678-1.438 3.678-3.3 0-1.59-.947-2.51-2.956-3.028l-.722-.187V3.467c1.122.11 1.879.714 2.07 1.616h1.47c-.166-1.6-1.54-2.748-3.54-2.875V1H7.591v1.233c-1.939.23-3.27 1.472-3.27 3.156 0 1.454.966 2.483 2.661 2.917l.61.162v4.031c-1.149-.17-1.94-.8-2.131-1.718H4zm3.391-3.836c-1.043-.263-1.6-.825-1.6-1.616 0-.944.704-1.641 1.8-1.828v3.495l-.2-.05zm1.591 1.872c1.287.323 1.852.859 1.852 1.769 0 1.097-.826 1.828-2.2 1.939V8.73l.348.086z"/>
                </svg>
                <p>No fees configured</p>
                <small>Go to Fees page to add fees first</small>
            </div>
        `;
        return;
    }
    
    const filteredFees = availableFees.filter(fee => {
        const search = searchTerm.toLowerCase();
        return fee.name.toLowerCase().includes(search) ||
               (fee.description && fee.description.toLowerCase().includes(search));
    });
    
    if (filteredFees.length === 0) {
        body.innerHTML = `
            <div class="no-fees-message">
                <p>No fees found matching "${searchTerm}"</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    filteredFees.forEach(fee => {
        const isSelected = tempSelectedFees.has(fee.id);
        html += `
            <div class="fee-option ${isSelected ? 'selected' : ''}" data-fee-id="${fee.id}" onclick="toggleFeeSelection(${fee.id})">
                <div class="fee-option-checkbox"></div>
                <div class="fee-option-info">
                    <div class="fee-option-name">${fee.name}</div>
                    ${fee.description ? `<div class="fee-option-description">${fee.description}</div>` : ''}
                </div>
                <div class="fee-option-price">₱${parseFloat(fee.amount).toFixed(2)}</div>
            </div>
        `;
    });
    
    body.innerHTML = html;
}

function toggleFeeSelection(feeId) {
    if (tempSelectedFees.has(feeId)) {
        tempSelectedFees.delete(feeId);
    } else {
        tempSelectedFees.add(feeId);
    }
    
    const feeOption = document.querySelector(`.fee-option[data-fee-id="${feeId}"]`);
    if (feeOption) {
        feeOption.classList.toggle('selected');
    }
}

function confirmFeeSelection() {
    tempSelectedFees.forEach(feeId => {
        if (!selectedFeesMap.has(feeId)) {
            const fee = availableFees.find(f => f.id === feeId);
            if (fee) {
                selectedFeesMap.set(feeId, {
                    fee: fee,
                    quantity: 1
                });
            }
        }
    });
    
    const toRemove = [];
    selectedFeesMap.forEach((data, feeId) => {
        if (!tempSelectedFees.has(feeId)) {
            toRemove.push(feeId);
        }
    });
    toRemove.forEach(feeId => selectedFeesMap.delete(feeId));
    
    renderSelectedFees();
    updateSummary();
    closeFeeSelector();
}

function renderSelectedFees() {
    const container = document.getElementById('selectedFeesList');
    
    if (!container) {
        console.error('❌ Selected fees list container not found!');
        return;
    }
    
    if (selectedFeesMap.size === 0) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    selectedFeesMap.forEach((data, feeId) => {
        const { fee, quantity } = data;
        const total = quantity * parseFloat(fee.amount);
        
        html += `
            <div class="selected-fee-item">
                <div class="selected-fee-name">${fee.name}</div>
                <div class="selected-fee-qty">
                    <button type="button" onclick="decreaseFeeQuantity(${feeId})">−</button>
                    <input type="number" value="${quantity}" min="1" readonly>
                    <button type="button" onclick="increaseFeeQuantity(${feeId})">+</button>
                </div>
                <div class="selected-fee-price">₱${total.toFixed(2)}</div>
                <button type="button" class="selected-fee-remove" onclick="removeFeeFromList(${feeId})">×</button>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function increaseFeeQuantity(feeId) {
    if (selectedFeesMap.has(feeId)) {
        const data = selectedFeesMap.get(feeId);
        data.quantity++;
        selectedFeesMap.set(feeId, data);
        renderSelectedFees();
        updateSummary();
    }
}

function decreaseFeeQuantity(feeId) {
    if (selectedFeesMap.has(feeId)) {
        const data = selectedFeesMap.get(feeId);
        if (data.quantity > 1) {
            data.quantity--;
            selectedFeesMap.set(feeId, data);
            renderSelectedFees();
            updateSummary();
        }
    }
}

function removeFeeFromList(feeId) {
    selectedFeesMap.delete(feeId);
    renderSelectedFees();
    updateSummary();
}

function updateSummary() {
    const breakdownDiv = document.getElementById('amountBreakdown');
    const totalDiv = document.getElementById('totalAmount');
    
    if (!breakdownDiv || !totalDiv) return;
    
    let total = 0;
    let breakdownHTML = '';
    
    selectedFeesMap.forEach((data, feeId) => {
        const { fee, quantity } = data;
        const itemTotal = quantity * parseFloat(fee.amount);
        total += itemTotal;
        
        breakdownHTML += `
            <div class="amount-item">
                <span>${fee.name}(${quantity})</span>
                <span>₱${itemTotal.toFixed(2)}</span>
            </div>
        `;
    });
    
    breakdownDiv.innerHTML = breakdownHTML || '<div class="amount-item"><span>No items</span><span>₱0.00</span></div>';
    totalDiv.textContent = `₱${total.toFixed(2)}`;
}

// =================== DRAG AND DROP ===================

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

function closeModalFunc() {
    const modal = document.getElementById('addItemModal');
    const addItemForm = document.getElementById('addItemForm');
    
    modal.classList.remove('active');
    addItemForm.reset();
    
    const approvalActions = document.querySelector('.approval-actions');
    if (approvalActions) {
        approvalActions.remove();
    }
    
    const statusBadge = document.querySelector('.status-badge');
    if (statusBadge) {
        statusBadge.remove();
    }
    
    selectedFeesMap.clear();
    renderSelectedFees();
    updateSummary();
}

// =================== CLOSE ALL DROPDOWNS WHEN CLICKING OUTSIDE ===================
document.addEventListener('click', function(event) {
    // Close card menu dropdowns
    if (!event.target.closest('.card-menu')) {
        document.querySelectorAll('.card-menu-dropdown').forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    }
    
    // Close reports dropdown
    const reportsContainer = document.querySelector('.reports-dropdown-container');
    if (reportsContainer && !reportsContainer.contains(event.target)) {
        const btn = document.getElementById('reportsDropdownBtn');
        const menu = document.getElementById('reportsDropdownMenu');
        if (btn && menu) {
            btn.classList.remove('active');
            menu.classList.remove('active');
        }
    }
});

// =================== DOM CONTENT LOADED ===================
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing dashboard...');
    
    // Initialize fees
    loadAvailableFees();
    
    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            document.querySelectorAll('.card').forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(searchTerm) ? 'block' : 'none';
            });
        });
    }
    
    // Drag and drop
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
    
    // Modal functionality
    const modal = document.getElementById('addItemModal');
    const addButtons = document.querySelectorAll('.add-card-btn');
    const closeModalBtn = document.getElementById('closeModal');
    const addItemForm = document.getElementById('addItemForm');

    addButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const status = this.dataset.status;
            document.getElementById('item_status').value = status;
            modal.classList.add('active');
            setCurrentDate();
            generateChargeNumber();
            loadLibrarianSignature();
            
            selectedFeesMap.clear();
            renderSelectedFees();
            updateSummary();
        });
    });

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModalFunc);
    }

    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModalFunc();
            }
        });
    }
    
    // Form submission
    if (addItemForm) {
        addItemForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (selectedFeesMap.size === 0) {
                alert('⚠️ Please add at least one fee');
                return;
            }
            
            const items = [];
            selectedFeesMap.forEach((data, feeId) => {
                items.push({
                    description: data.fee.name,
                    quantity: data.quantity,
                    amount: parseFloat(data.fee.amount)
                });
            });
            
            const total = items.reduce((sum, item) => sum + (item.quantity * item.amount), 0);
            const dbDate = document.getElementById('chargeDate').getAttribute('data-db-date');
            const signatureImg = document.querySelector('.librarian-signature-img');
            const librarianSignature = signatureImg ? signatureImg.src : null;
            
            const formData = {
                name: document.getElementById('student_name').value,
                student_no: document.getElementById('student_no').value,
                program: document.getElementById('program').value,
                term: document.getElementById('term').value,
                academic_year: document.getElementById('academic_year').value || '2025-2026',
                items: items,
                total: total,
                charged_by: document.getElementById('charged_by').value,
                librarian_signature: librarianSignature,
                status: document.getElementById('item_status').value,
                charge_number: document.getElementById('chargeNumber').textContent,
                date: dbDate
            };
            
            const submitBtn = this.querySelector('.btn-save');
            submitBtn.disabled = true;
            submitBtn.textContent = 'SAVING...';
            
            fetch('/create-billing/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json().then(data => ({
                status: response.status,
                data: data
            })))
            .then(result => {
                if (result.status === 200 && result.data.success) {
                    alert('✅ Billing form created successfully!');
                    location.reload();
                } else {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'SAVE';
                    alert('❌ Error: ' + (result.data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Fetch error:', error);
                submitBtn.disabled = false;
                submitBtn.textContent = 'SAVE';
                alert('❌ An error occurred');
            });
        });
    }
    
    // Fee selector event listeners
    const btnAddFeeItem = document.getElementById('btnAddFeeItem');
    if (btnAddFeeItem) {
        btnAddFeeItem.addEventListener('click', openFeeSelector);
    }
    
    const closeFeeSelectorBtn = document.getElementById('closeFeeSelector');
    if (closeFeeSelectorBtn) {
        closeFeeSelectorBtn.addEventListener('click', closeFeeSelector);
    }
    
    const cancelFeeSelectionBtn = document.getElementById('cancelFeeSelection');
    if (cancelFeeSelectionBtn) {
        cancelFeeSelectionBtn.addEventListener('click', closeFeeSelector);
    }
    
    const confirmFeeSelectionBtn = document.getElementById('confirmFeeSelection');
    if (confirmFeeSelectionBtn) {
        confirmFeeSelectionBtn.addEventListener('click', confirmFeeSelection);
    }
    
    const feeSearchInput = document.getElementById('feeSearchInput');
    if (feeSearchInput) {
        feeSearchInput.addEventListener('input', function(e) {
            renderFeeOptions(e.target.value);
        });
    }
    
    const feeSelectorOverlay = document.getElementById('feeSelectorOverlay');
    if (feeSelectorOverlay) {
        feeSelectorOverlay.addEventListener('click', function(e) {
            if (e.target === this) {
                closeFeeSelector();
            }
        });
    }
    
    // Initialize summary
    updateSummary();
    
    console.log('✅ Main dashboard script loaded');
});