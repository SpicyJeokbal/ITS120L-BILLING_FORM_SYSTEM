// frontend/static/js/billing_autocomplete.js

// =================== STUDENT AUTOCOMPLETE ===================

let studentsCache = [];
let isManualEntry = false;

// Fetch all students when page loads
document.addEventListener('DOMContentLoaded', function() {
    fetchStudents();
});

async function fetchStudents() {
    try {
        const response = await fetch('/students/list/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        const result = await response.json();
        if (result.success) {
            studentsCache = result.students;
            console.log(`✅ Loaded ${studentsCache.length} students for autocomplete`);
        }
    } catch (error) {
        console.error('Error fetching students:', error);
    }
}

// Setup student number input with autocomplete
function setupStudentAutocomplete() {
    const studentNoInput = document.getElementById('student_no');
    if (!studentNoInput) {
        console.error('❌ Student number input not found!');
        return;
    }

    console.log('✅ Setting up autocomplete on student_no field');

    // Create autocomplete dropdown if it doesn't exist
    let dropdown = document.getElementById('studentAutocompleteDropdown');
    if (!dropdown) {
        dropdown = document.createElement('div');
        dropdown.className = 'student-autocomplete-dropdown';
        dropdown.id = 'studentAutocompleteDropdown';
        studentNoInput.parentElement.appendChild(dropdown);
    }

    // Remove any existing event listeners by cloning and replacing
    const newInput = studentNoInput.cloneNode(true);
    studentNoInput.parentNode.replaceChild(newInput, studentNoInput);
    
    // Re-get the element
    const input = document.getElementById('student_no');

    // Listen for input changes
    input.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        console.log('Input changed:', query);
        
        if (query.length === 0) {
            hideAutocompleteDropdown();
            clearStudentFields();
            isManualEntry = false;
            return;
        }

        // Search students
        const matches = searchStudents(query);
        
        console.log('Found matches:', matches.length);
        
        if (matches.length > 0) {
            showAutocompleteDropdown(matches);
        } else {
            hideAutocompleteDropdown();
            // Allow manual entry
            isManualEntry = true;
            showManualEntryHint();
        }
    });

    // Listen for blur after a delay (to allow click on dropdown)
    input.addEventListener('blur', function() {
        setTimeout(() => {
            hideAutocompleteDropdown();
        }, 200);
    });

    // Check on Enter key
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            const query = e.target.value.trim();
            const matches = searchStudents(query);
            
            if (matches.length === 1) {
                selectStudent(matches[0]);
            } else if (matches.length === 0) {
                isManualEntry = true;
                showManualEntryHint();
            }
        }
    });

    // Also check when field loses focus (for exact match)
    input.addEventListener('change', function() {
        const query = this.value.trim();
        if (query.length > 0) {
            const student = studentsCache.find(s => s.student_no === query);
            if (student) {
                selectStudent(student);
            }
        }
    });
}

function searchStudents(query) {
    if (!query) return [];
    
    query = query.toLowerCase();
    
    return studentsCache.filter(student => {
        const studentNo = student.student_no.toLowerCase();
        const name = student.name.toLowerCase();
        
        return studentNo.includes(query) || name.includes(query);
    }).slice(0, 5); // Limit to 5 results
}

function showAutocompleteDropdown(matches) {
    const dropdown = document.getElementById('studentAutocompleteDropdown');
    if (!dropdown) return;

    dropdown.innerHTML = '';
    dropdown.style.display = 'block';

    matches.forEach(student => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `
            <div class="autocomplete-student-no">${student.student_no}</div>
            <div class="autocomplete-student-name">${student.name}</div>
            <div class="autocomplete-student-info">${student.program} - ${student.term} - ${student.academic_year}</div>
        `;
        
        item.addEventListener('click', function() {
            selectStudent(student);
        });
        
        dropdown.appendChild(item);
    });
}

function hideAutocompleteDropdown() {
    const dropdown = document.getElementById('studentAutocompleteDropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

function selectStudent(student) {
    console.log('✅ Selected student:', student);
    
    // Fill in the form fields
    document.getElementById('student_no').value = student.student_no;
    document.getElementById('student_name').value = student.name;
    document.getElementById('program').value = student.program;
    document.getElementById('term').value = student.term;
    document.getElementById('academic_year').value = student.academic_year;
    
    // Make fields read-only to indicate auto-filled (but still allow editing)
    const fields = ['student_name', 'program', 'term', 'academic_year'];
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.add('autofilled');
        }
    });
    
    // Add visual indicator
    showEditButton();
    
    // Hide dropdown
    hideAutocompleteDropdown();
    hideManualEntryHint();
    
    isManualEntry = false;
}

function clearStudentFields() {
    // Only clear if not manually entered
    if (!isManualEntry) {
        document.getElementById('student_name').value = '';
        document.getElementById('program').value = '';
        document.getElementById('term').value = '';
        document.getElementById('academic_year').value = '';
    }
    
    // Remove autofilled styling
    const fields = ['student_name', 'program', 'term', 'academic_year'];
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.remove('autofilled');
        }
    });
    
    hideEditButton();
}

function showEditButton() {
    let editBtn = document.getElementById('editStudentInfoBtn');
    if (!editBtn) {
        editBtn = document.createElement('button');
        editBtn.id = 'editStudentInfoBtn';
        editBtn.type = 'button';
        editBtn.className = 'btn-edit-student-info';
        editBtn.innerHTML = '✏️ Edit Student Info';
        editBtn.onclick = enableManualEdit;
        
        const studentNameField = document.getElementById('student_name');
        if (studentNameField && studentNameField.parentElement) {
            studentNameField.parentElement.appendChild(editBtn);
        }
    }
    editBtn.style.display = 'inline-block';
}

function hideEditButton() {
    const editBtn = document.getElementById('editStudentInfoBtn');
    if (editBtn) {
        editBtn.style.display = 'none';
    }
}

function enableManualEdit() {
    const fields = ['student_name', 'program', 'term', 'academic_year'];
    fields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.remove('autofilled');
        }
    });
    
    isManualEntry = true;
    hideEditButton();
    
    alert('You can now edit the student information manually.');
}

function showManualEntryHint() {
    let hint = document.getElementById('manualEntryHint');
    if (!hint) {
        hint = document.createElement('div');
        hint.id = 'manualEntryHint';
        hint.className = 'manual-entry-hint';
        hint.innerHTML = '⚠️ Student not found. You can manually enter their information below.';
        
        const studentNoField = document.getElementById('student_no');
        if (studentNoField && studentNoField.parentElement) {
            studentNoField.parentElement.appendChild(hint);
        }
    }
    hint.style.display = 'block';
}

function hideManualEntryHint() {
    const hint = document.getElementById('manualEntryHint');
    if (hint) {
        hint.style.display = 'none';
    }
}

// Initialize autocomplete when modal is opened
const billingModal = document.getElementById('addItemModal'); // CHANGED: renamed from 'modal' to 'billingModal'
if (billingModal) {
    // Watch for modal opening
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                if (billingModal.classList.contains('active')) {
                    console.log('📋 Modal opened, setting up autocomplete');
                    setTimeout(() => {
                        setupStudentAutocomplete();
                    }, 100);
                }
            }
        });
    });
    
    observer.observe(billingModal, { attributes: true });
}

// Also setup when add buttons are clicked
document.addEventListener('DOMContentLoaded', function() {
    const addButtons = document.querySelectorAll('.add-card-btn');
    addButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            setTimeout(() => {
                setupStudentAutocomplete();
            }, 100);
        });
    });
});

console.log('✅ Student autocomplete loaded');