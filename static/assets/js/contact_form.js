document.getElementById('contact-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Get the form and message box elements
    const form = this;
    const messageBox = document.getElementById('message-box');
    const submitBtn = document.getElementById('submit-btn');
    
    // Disable submit button and show loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';
    
    // Get form data
    const formData = new FormData(form);
    
    // Send the request
    fetch('/submit-contact/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Show message with fade-in effect
        messageBox.innerHTML = `
            <div class="alert ${data.status === 'success' ? 'alert-success' : 'alert-danger'} fade-in">
                ${data.message}
            </div>
        `;

        // Trigger fade-in animation
        setTimeout(() => {
            document.querySelector('.fade-in').classList.add('fade-visible');
        }, 50);

        // Reset form if successful
        if (data.status === 'success') {
            form.reset();
        }

        // Hide message after 3 seconds with fade-out effect
        setTimeout(() => {
            document.querySelector('.fade-in').classList.add('fade-out');
            setTimeout(() => {
                messageBox.innerHTML = ''; // Remove message completely
            }, 500);
        }, 3000);
    })
    .catch(error => {
        messageBox.innerHTML = `
            <div class="alert alert-danger fade-in">
                An error occurred. Please try again.
            </div>
        `;

        // Trigger fade-in animation
        setTimeout(() => {
            document.querySelector('.fade-in').classList.add('fade-visible');
        }, 50);

        // Hide message after 3 seconds with fade-out effect
        setTimeout(() => {
            document.querySelector('.fade-in').classList.add('fade-out');
            setTimeout(() => {
                messageBox.innerHTML = ''; // Remove message completely
            }, 500);
        }, 3000);
    })
    .finally(() => {
        // Re-enable submit button
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Details';
    });
});

// Add styles dynamically for fade effects
const style = document.createElement('style');
style.textContent = `
    .fade-in {
        opacity: 0;
        transform: translateY(-10px);
        transition: opacity 0.5s ease-in, transform 0.5s ease-in;
    }
    
    .fade-visible {
        opacity: 1;
        transform: translateY(0);
    }

    .fade-out {
        opacity: 0;
        transform: translateY(-10px);
        transition: opacity 0.5s ease-out, transform 0.5s ease-out;
    }
`;
document.head.appendChild(style);
