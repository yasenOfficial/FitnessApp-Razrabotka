// GameFit Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
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
        exerciseForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const exerciseType = document.getElementById('exercise-type').value;
            const exerciseCount = document.getElementById('exercise-count').value;
            const exerciseIntensity = document.getElementById('exercise-intensity').value;
            
            if (!exerciseType || !exerciseCount) {
                alert('Please fill out all fields');
                return;
            }
            
            // Calculate points based on exercise type, count and intensity
            let basePoints = 0;
            switch(exerciseType) {
                case 'pushup':
                    basePoints = exerciseCount * 0.5;
                    break;
                case 'situp':
                    basePoints = exerciseCount * 0.3;
                    break;
                case 'squat':
                    basePoints = exerciseCount * 0.4;
                    break;
                case 'pullup':
                    basePoints = exerciseCount * 1;
                    break;
                case 'burpee':
                    basePoints = exerciseCount * 1.5;
                    break;
                case 'plank':
                    basePoints = exerciseCount * 0.1; // Per second
                    break;
                case 'run':
                    basePoints = exerciseCount * 2; // Per minute
                    break;
                default:
                    basePoints = exerciseCount * 0.5;
            }
            
            // Apply intensity multiplier
            const pointsEarned = Math.round(basePoints * parseFloat(exerciseIntensity));
            
            // Send data to server (to be implemented)
            fetch('/api/log-exercise', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    exercise_type: exerciseType,
                    count: exerciseCount,
                    intensity: exerciseIntensity,
                    points: pointsEarned
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message with points
                    alert(`Exercise logged! You earned ${pointsEarned} points!`);
                    
                    // Close modal
                    modal.style.display = 'none';
                    document.body.style.overflow = 'auto';
                    
                    // Refresh page to update stats
                    location.reload();
                } else {
                    alert('Error: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error logging exercise. Please try again.');
            });
        });
    }
    
    // Logout functionality
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Clear token
            document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            
            // Redirect to home
            window.location.href = '/';
        });
    }
    
    // Add animation effects
    const animatedElements = document.querySelectorAll('.card, .stats-card, .achievement');
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fadeIn');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    animatedElements.forEach(el => {
        observer.observe(el);
    });
    
    // Confetti effect for rank up (placeholder for future implementation)
    // This would be triggered when user ranks up after logging exercise
    function launchConfetti() {
        // Placeholder for confetti animation
        console.log("Confetti launched for rank up!");
    }
    });