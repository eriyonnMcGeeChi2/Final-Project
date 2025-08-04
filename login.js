// File: script.js

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('login-form').addEventListener('submit', async function(e) {
    e.preventDefault(); // Prevent default form submission

    const form = e.target;
    const formData = new FormData(form);
    const params = new URLSearchParams(formData).toString();

    const response = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: params,
        credentials: 'include' // Include cookies in the request
    });

    const text = await response.text();

    if (text.includes('Login failed')) {
        // On success, redirect to the index page
        document.getElementById('error-message').textContent = 'Login failed. Please try again.'; // Clear any previous error message
    }
    else if (text.includes('Success') || response.status === 200) {
        window.location = '/';
    }
    });



    
    // Create account form handler
    const createForm = document.getElementById('create-account-form');
    if (createForm) {
        createForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const form = e.target;
            const formData = new FormData(form);

            // Check password match
            if (formData.get('new_password') !== formData.get('confirm_password')) {
                document.getElementById('create-error-message').textContent = 'Passwords do not match.';
                return;
            }

            // Rename fields to match server expectations
            formData.set('username', formData.get('new_username'));
            formData.set('password', formData.get('new_password'));

            // Remove fields not needed by server
            formData.delete('new_username');
            formData.delete('new_password');
            formData.delete('confirm_password');

            const params = new URLSearchParams(formData);

            const response = await fetch('/api/create_account', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: params
            });

            const text = await response.text();

            if (text.includes('User created successfully')) {
                window.location = '/login';
            } else {
                document.getElementById('create-error-message').textContent = text;
            }
        });
    }
});