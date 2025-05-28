document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('exerciseLogModal');
    const closeModal = modal.querySelector('.close-modal');
    const exerciseCards = document.querySelectorAll('.exercise-card');
    const modalTitle = document.getElementById('modalExerciseTitle');
    const exerciseTypeInput = document.getElementById('exerciseType');
    const form = document.getElementById('exerciseLogForm');
    const exerciseSelect = document.getElementById('exerciseSelect');
    let progressChart = null;

    // Initialize progress chart
    function initChart(data) {
        const ctx = document.getElementById('progressChart').getContext('2d');
        if (progressChart) {
            progressChart.destroy();
        }

        // Find the maximum value for better scaling
        const maxCount = Math.max(...data.counts);
        console.log('Maximum count value:', maxCount);

        progressChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: data.exerciseLabel,
                    data: data.counts,
                    borderColor: getComputedStyle(document.documentElement).getPropertyValue('--secondary').trim(),
                    backgroundColor: getComputedStyle(document.documentElement).getPropertyValue('--secondary').trim() + '20',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f7f7f7'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Count: ${context.parsed.y.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#f7f7f7',
                            callback: function(value) {
                                if (value >= 1000000) {
                                    return (value / 1000000).toFixed(1) + 'M';
                                } else if (value >= 1000) {
                                    return (value / 1000).toFixed(1) + 'K';
                                }
                                return value;
                            }
                        },
                        suggestedMax: maxCount * 1.1 // Add 10% padding to the top
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#f7f7f7'
                        }
                    }
                }
            }
        });
    }

    // Fetch exercise data and update chart
    function updateChart(exerciseType) {
        console.log('Fetching stats for exercise type:', exerciseType);
        fetch(`/api/v1/exercises/${exerciseType}/stats`)
            .then(response => response.json())
            .then(data => {
                console.log('Received stats data:', data);
                // Verify the data is being processed correctly
                console.log('Data validation:');
                console.log('Number of dates:', data.dates.length);
                console.log('Number of counts:', data.counts.length);
                console.log('Sample counts:', data.counts.slice(-5));
                
                initChart({
                    labels: data.dates,
                    counts: data.counts,
                    exerciseLabel: exerciseSelect.options[exerciseSelect.selectedIndex].text
                });
            })
            .catch(error => {
                console.error('Error fetching exercise stats:', error);
            });
    }

    // Exercise selector change handler
    exerciseSelect.addEventListener('change', function() {
        updateChart(this.value);
    });

    // Initial chart load
    updateChart(exerciseSelect.value);

    // Open modal when clicking on exercise card
    exerciseCards.forEach(card => {
        card.addEventListener('click', function() {
            const exerciseType = this.dataset.exerciseType;
            const exerciseLabel = this.dataset.exerciseLabel;
            
            modalTitle.innerHTML = `<i class="fas fa-dumbbell"></i> Log ${exerciseLabel}`;
            exerciseTypeInput.value = exerciseType;
            
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    });

    // Close modal functionality
    closeModal.addEventListener('click', function() {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    });

    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    // Form submission
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        const exerciseType = formData.get('exerciseType');
        const count = parseInt(formData.get('exerciseCount')) || 0;
        const date = formData.get('exerciseDate');

        if (count <= 0) {
            return;
        }

        const submitData = {
            type: exerciseType,
            count: count,
            date: date
        };
        console.log('Submitting exercise data:', submitData);

        // Submit to the API
        fetch('/api/v1/exercises', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(submitData)
        })
        .then(response => response.json())
        .then(data => {
            console.log('Exercise submission response:', data);
            // Close modal and refresh page
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
            location.reload();
        })
        .catch(error => {
            console.error('Error logging exercise:', error);
        });
    });

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 3000);
    });
}); 