// frontend/static/js/signature_settings.js

let canvas, ctx;
let isDrawing = false;
let hasDrawn = false;

// Initialize canvas on page load
document.addEventListener('DOMContentLoaded', function() {
    canvas = document.getElementById('signatureCanvas');
    if (!canvas) return;
    
    ctx = canvas.getContext('2d');
    
    // Set up canvas style
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Mouse events
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);
    
    // Touch events for mobile/tablet
    canvas.addEventListener('touchstart', handleTouchStart);
    canvas.addEventListener('touchmove', handleTouchMove);
    canvas.addEventListener('touchend', stopDrawing);
    
    console.log('✅ Signature canvas initialized');
});

// =================== DRAWING FUNCTIONS ===================
function startDrawing(e) {
    isDrawing = true;
    hasDrawn = true;
    const rect = canvas.getBoundingClientRect();
    ctx.beginPath();
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
}

function draw(e) {
    if (!isDrawing) return;
    
    const rect = canvas.getBoundingClientRect();
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.stroke();
}

function stopDrawing() {
    isDrawing = false;
}

function handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
}

// =================== UI FUNCTIONS ===================
function showSignaturePad() {
    document.getElementById('signatureEditor').style.display = 'block';
    clearSignature();
}

function hideSignaturePad() {
    document.getElementById('signatureEditor').style.display = 'none';
    clearSignature();
}

function clearSignature() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    hasDrawn = false;
}

// =================== SAVE SIGNATURE ===================
async function saveSignature() {
    if (!hasDrawn) {
        alert('⚠️ Please draw your signature first.');
        return;
    }
    
    // Check if signature is not just a blank canvas
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const pixels = imageData.data;
    let hasContent = false;
    
    for (let i = 0; i < pixels.length; i += 4) {
        if (pixels[i + 3] > 0) { // Check alpha channel
            hasContent = true;
            break;
        }
    }
    
    if (!hasContent) {
        alert('⚠️ Please draw your signature. The canvas is blank.');
        return;
    }
    
    // Convert to compressed image
    const signatureBlob = await getCompressedSignature();
    
    if (!signatureBlob) {
        alert('❌ Error creating signature image.');
        return;
    }
    
    // Check size (should be under 100KB)
    if (signatureBlob.size > 100 * 1024) {
        alert('⚠️ Signature file too large. Please try a simpler signature.');
        return;
    }
    
    console.log(`Signature size: ${(signatureBlob.size / 1024).toFixed(2)}KB`);
    
    // Prepare form data
    const formData = new FormData();
    formData.append('signature', signatureBlob, 'signature.jpg');
    
    // Show loading state
    const saveBtn = document.querySelector('.btn-save-signature');
    const originalText = saveBtn.innerHTML;
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<svg width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M8 3a5 5 0 1 0 0 10A5 5 0 0 0 8 3z"/></svg> Saving...';
    
    try {
        const response = await fetch('/signature-settings/save/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✅ Signature saved successfully!');
            location.reload();
        } else {
            alert('❌ ' + (result.message || 'Failed to save signature'));
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    } catch (error) {
        console.error('Error saving signature:', error);
        alert('❌ An error occurred while saving your signature.');
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
}

// =================== IMAGE COMPRESSION ===================
async function getCompressedSignature() {
    // Create a smaller canvas for compression
    const compressedCanvas = document.createElement('canvas');
    const compressedCtx = compressedCanvas.getContext('2d');
    
    // Set smaller dimensions (signatures don't need to be huge)
    compressedCanvas.width = 400;
    compressedCanvas.height = 150;
    
    // Fill with white background
    compressedCtx.fillStyle = 'white';
    compressedCtx.fillRect(0, 0, compressedCanvas.width, compressedCanvas.height);
    
    // Draw scaled signature
    compressedCtx.drawImage(canvas, 0, 0, compressedCanvas.width, compressedCanvas.height);
    
    // Convert to blob with compression
    return new Promise((resolve) => {
        compressedCanvas.toBlob(
            (blob) => {
                resolve(blob);
            },
            'image/jpeg',  // JPEG is smaller than PNG
            0.7            // 70% quality
        );
    });
}

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

console.log('✅ Signature settings page loaded');