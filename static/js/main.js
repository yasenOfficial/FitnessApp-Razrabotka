// GameFit Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Global error handler for fetch requests
    async function handleFetchResponse(response) {
        const contentType = response.headers.get('content-type');
        const isJson = contentType && contentType.includes('application/json');
        const data = isJson ? await response.json() : null;

        if (!response.ok) {
            // Handle specific error cases
            switch (response.status) {
                case 401:
                    // For missing cookie or expired session, redirect silently
                    if (data?.message?.includes('Missing cookie')) {
                        window.location.href = '/auth';
                        return;
                    }
                    // For other unauthorized cases
                    showError('Please log in to continue');
                    setTimeout(() => {
                        window.location.href = '/auth';
                    }, 2000);
                    break;
                case 403:
                    // Forbidden
                    showError('You do not have permission to perform this action');
                    break;
                case 404:
                    // Not Found
                    showError('The requested resource was not found');
                    break;
                case 500:
                    // Server Error
                    showError('An internal server error occurred. Please try again later.');
                    break;
                default:
                    // Other errors
                    showError(data?.message || 'An unexpected error occurred');
            }
            throw new Error(data?.message || 'Request failed');
        }
        return data;
    }

    // Global error message display
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-toast';
        errorDiv.innerHTML = `
            <div class="error-content">
                <span class="error-message">${message}</span>
                <button class="close-btn">&times;</button>
            </div>
        `;
        document.body.appendChild(errorDiv);

        // Add close button functionality
        const closeBtn = errorDiv.querySelector('.close-btn');
        closeBtn.addEventListener('click', () => errorDiv.remove());

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(errorDiv)) {
                errorDiv.remove();
            }
        }, 5000);
    }

    // Add error toast styles
    const style = document.createElement('style');
    style.textContent = `
        .error-toast {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }

        .error-content {
            background-color: #ff4757;
            color: white;
            padding: 1rem 2rem;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .close-btn {
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

    // Modal functionality
    const modal = document.getElementById('exerciseModal');
    const logExerciseBtn = document.getElementById('log-exercise-btn');
    const closeModal = document.querySelector('.close-modal');
    if (logExerciseBtn) {
        logExerciseBtn.addEventListener('click', function() {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden'; // Prevent scrolling when modal is open
        });
    }
    
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto'; // Enable scrolling again
        });
    }
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });
    
    // Exercise form submission
    const exerciseForm = document.getElementById('exercise-form');
    if (exerciseForm) {
        exerciseForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const exerciseType = document.getElementById('exercise-type').value;
            const exerciseCount = parseInt(document.getElementById('exercise-count').value);
            const exerciseIntensity = parseFloat(document.getElementById('exercise-intensity').value);
            
            if (!exerciseType || isNaN(exerciseCount) || exerciseCount <= 0) {
                showError('Please fill in all required fields correctly');
                return;
            }

            try {
                const response = await fetch('/api/log-exercise', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        exercise_type: exerciseType,
                        count: exerciseCount,
                        intensity: exerciseIntensity
                    }),
                });

                const data = await handleFetchResponse(response);
                if (data.success) {
                    // Show success message
                    const successDiv = document.createElement('div');
                    successDiv.className = 'success-toast';
                    successDiv.textContent = `Exercise logged! You earned ${data.points} points!`;
                    document.body.appendChild(successDiv);
                    
                    // Close modal and refresh page
                    const modal = document.getElementById('exercise-modal');
                    if (modal) {
                        modal.style.display = 'none';
                        document.body.style.overflow = 'auto';
                    }
                    setTimeout(() => location.reload(), 1000);
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
    
    // Logout functionality
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            
            try {
                const response = await fetch('/api/logout', {
                    method: 'POST'
                });
                await handleFetchResponse(response);
                window.location.href = '/';
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
    
    // Add animation effects
    const animatedElements = document.querySelectorAll('.card, .stats-card, .achievement');
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    animatedElements.forEach(el => observer.observe(el));
    
    // Confetti effect for rank up (placeholder for future implementation)
    // This would be triggered when user ranks up after logging exercise
    function launchConfetti() {
        // Placeholder for confetti animation
        console.log("Confetti launched for rank up!");
    }
});