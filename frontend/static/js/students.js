// frontend/static/js/students.js

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
function openModal(modalId) {
    document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
    const form = document.getElementById(modalId).querySelector('form');
    if (form) form.reset();
}

// Close modal on background click
document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal(this.id);
        }
    });
});

// =================== IMPORT EXCEL ===================
let excelData = [];

document.getElementById('importStudentsBtn').addEventListener('click', function() {
    openModal('importModal');
});

// Drag and drop
const uploadArea = document.getElementById('uploadArea');
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#0052cc';
    uploadArea.style.background = '#deebff';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = '#dfe1e6';
    uploadArea.style.background = '';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#dfe1e6';
    uploadArea.style.background = '';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// File input change
document.getElementById('excelFile').addEventListener('change', function(e) {
    if (e.target.files.length > 0) {
        handleFile(e.target.files[0]);
    }
});

function handleFile(file) {
    if (!file.name.match(/\.(xlsx|xls)$/)) {
        alert('Please upload an Excel file (.xlsx or .xls)');
        return;
    }

    document.getElementById('fileName').textContent = file.name;

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            const jsonData = XLSX.utils.sheet_to_json(firstSheet);

            processExcelData(jsonData);
        } catch (error) {
            alert('Error reading Excel file: ' + error.message);
        }
    };
    reader.readAsArrayBuffer(file);
}

function processExcelData(data) {
    excelData = [];

    data.forEach((row, index) => {
        // Try different possible column name variations
        const studentNo = row['Student Number'] || row['student_number'] || row['StudentNo'] || row['Student No'];
        const name = row['Name'] || row['name'] || row['Student Name'];
        const program = row['Program'] || row['program'] || row['Course'];
        const term = row['Term'] || row['term'] || row['Semester'];
        const academicYear = row['Academic Year'] || row['academic_year'] || row['AY'] || row['Year'];

        if (studentNo && name) {
            excelData.push({
                student_no: String(studentNo).trim(),
                name: String(name).trim().toUpperCase(),
                program: String(program || '').trim().toUpperCase(),
                term: String(term || '').trim(),
                academic_year: String(academicYear || '2025-2026').trim()
            });
        }
    });

    if (excelData.length === 0) {
        alert('No valid student data found in Excel file. Please check the column names.');
        return;
    }

    // Show preview
    showPreview(excelData);
    document.getElementById('importSubmitBtn').disabled = false;
}

function showPreview(data) {
    const previewDiv = document.getElementById('importPreview');
    const previewTable = document.getElementById('previewTable');
    const previewCount = document.getElementById('previewCount');

    previewCount.textContent = data.length;

    let html = '<table class="example-table"><thead><tr>';
    html += '<th>Student Number</th><th>Name</th><th>Program</th><th>Term</th><th>Academic Year</th>';
    html += '</tr></thead><tbody>';

    // Show first 5 rows
    data.slice(0, 5).forEach(student => {
        html += '<tr>';
        html += `<td>${student.student_no}</td>`;
        html += `<td>${student.name}</td>`;
        html += `<td>${student.program}</td>`;
        html += `<td>${student.term}</td>`;
        html += `<td>${student.academic_year}</td>`;
        html += '</tr>';
    });

    if (data.length > 5) {
        html += `<tr><td colspan="5" style="text-align: center; color: #5e6c84;">... and ${data.length - 5} more students</td></tr>`;
    }

    html += '</tbody></table>';
    previewTable.innerHTML = html;
    previewDiv.style.display = 'block';
}

// Submit import
document.getElementById('importForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    if (excelData.length === 0) {
        alert('No data to import');
        return;
    }

    const submitBtn = document.getElementById('importSubmitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Importing...';

    try {
        const response = await fetch('/students/upload/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ students: excelData })
        });

        const result = await response.json();

        if (result.success) {
            alert(`Successfully imported ${result.imported} students!`);
            location.reload();
        } else {
            alert('' + (result.message || 'Error importing students'));
        }
    } catch (error) {
        alert('An error occurred: ' + error.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Import Students';
    }
});

// =================== ADD/EDIT STUDENT ===================
document.getElementById('addStudentBtn').addEventListener('click', function() {
    document.getElementById('studentModalTitle').textContent = 'Add Student';
    document.getElementById('studentForm').reset();
    document.getElementById('originalStudentNo').value = '';
    openModal('studentModal');
});

function editStudent(studentNo, name, program, term, academicYear) {
    document.getElementById('studentModalTitle').textContent = 'Edit Student';
    document.getElementById('originalStudentNo').value = studentNo;
    document.getElementById('studentNo').value = studentNo;
    document.getElementById('studentName').value = name;
    document.getElementById('studentProgram').value = program;
    document.getElementById('studentTerm').value = term;
    document.getElementById('studentAY').value = academicYear;
    openModal('studentModal');
}

document.getElementById('studentForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const submitBtn = document.getElementById('studentSubmitBtn');
    const originalStudentNo = document.getElementById('originalStudentNo').value;
    const isEdit = originalStudentNo !== '';

    submitBtn.disabled = true;
    submitBtn.textContent = isEdit ? 'Updating...' : 'Adding...';

    const data = {
        student_no: document.getElementById('studentNo').value,
        name: document.getElementById('studentName').value.toUpperCase(),
        program: document.getElementById('studentProgram').value.toUpperCase(),
        term: document.getElementById('studentTerm').value,
        academic_year: document.getElementById('studentAY').value
    };

    if (isEdit) {
        data.original_student_no = originalStudentNo;
    }

    try {
        const response = await fetch('/students/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert(isEdit ? 'Student updated successfully!' : 'Student added successfully!');
            location.reload();
        } else {
            alert('' + (result.message || 'Error saving student'));
        }
    } catch (error) {
        alert('An error occurred: ' + error.message);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Student';
    }
});

// =================== DELETE STUDENT ===================
function deleteStudent(studentNo, name) {
    if (!confirm(`Are you sure you want to delete ${name} (${studentNo})?`)) {
        return;
    }

    fetch('/students/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ student_no: studentNo })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('Student deleted successfully!');
            location.reload();
        } else {
            alert('' + (result.message || 'Error deleting student'));
        }
    })
    .catch(error => {
        alert('An error occurred: ' + error.message);
    });
}

// =================== SEARCH AND FILTER ===================
document.getElementById('searchInput').addEventListener('input', filterStudents);
document.getElementById('filterProgram').addEventListener('change', filterStudents);
document.getElementById('filterTerm').addEventListener('change', filterStudents);
document.getElementById('filterAY').addEventListener('change', filterStudents);

function filterStudents() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const filterProgram = document.getElementById('filterProgram').value;
    const filterTerm = document.getElementById('filterTerm').value;
    const filterAY = document.getElementById('filterAY').value;

    const rows = document.querySelectorAll('#studentsTableBody tr');

    rows.forEach(row => {
        const studentNo = row.cells[0]?.textContent.toLowerCase() || '';
        const name = row.cells[1]?.textContent.toLowerCase() || '';
        const program = row.cells[2]?.textContent || '';
        const term = row.cells[3]?.textContent || '';
        const ay = row.cells[4]?.textContent || '';

        const matchesSearch = studentNo.includes(searchTerm) || name.includes(searchTerm);
        const matchesProgram = !filterProgram || program === filterProgram;
        const matchesTerm = !filterTerm || term === filterTerm;
        const matchesAY = !filterAY || ay === filterAY;

        if (matchesSearch && matchesProgram && matchesTerm && matchesAY) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// =================== UPDATE STATS AND FILTERS ===================
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
    populateFilters();
});

function updateStats() {
    const rows = document.querySelectorAll('#studentsTableBody tr[data-student-id]');
    const programs = new Set();

    rows.forEach(row => {
        const program = row.cells[2]?.textContent;
        if (program) programs.add(program);
    });

    document.getElementById('totalPrograms').textContent = programs.size;
}

function populateFilters() {
    const rows = document.querySelectorAll('#studentsTableBody tr[data-student-id]');
    const programs = new Set();
    const academicYears = new Set();

    rows.forEach(row => {
        const program = row.cells[2]?.textContent;
        const ay = row.cells[4]?.textContent;
        if (program) programs.add(program);
        if (ay) academicYears.add(ay);
    });

    const programFilter = document.getElementById('filterProgram');
    const ayFilter = document.getElementById('filterAY');

    programs.forEach(program => {
        const option = document.createElement('option');
        option.value = program;
        option.textContent = program;
        programFilter.appendChild(option);
    });

    Array.from(academicYears).sort().reverse().forEach(ay => {
        const option = document.createElement('option');
        option.value = ay;
        option.textContent = ay;
        ayFilter.appendChild(option);
    });
}

console.log('Students page loaded');