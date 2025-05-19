// Authentication handling for GameFit
document.addEventListener('DOMContentLoaded', function() {
  const authForm = document.getElementById('auth-form');
  const formTitle = document.getElementById('form-title');
  const submitBtn = document.getElementById('submit-btn');
  const toggleBtn = document.getElementById('toggle-btn');
  let isLoginMode = true;
  
  if (toggleBtn && submitBtn && formTitle) {
      // Toggle between login and register modes
      toggleBtn.addEventListener('click', function() {
          isLoginMode = !isLoginMode;
          
          if (isLoginMode) {
              formTitle.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
              submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
              toggleBtn.textContent = 'New player? Register here';
          } else {
              formTitle.innerHTML = '<i class="fas fa-user-plus"></i> Register';
              submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Register';
              toggleBtn.textContent = 'Already have an account? Login';
          }
      });
  }
  
  if (authForm) {
      authForm.addEventListener('submit', function(e) {
          e.preventDefault();
          
          const username = document.getElementById('username').value;
          const password = document.getElementById('password').value;
          
          if (!username || !password) {
              showMessage('Please fill in all fields', 'error');
              return;
          }
          
          // Determine which API endpoint to use
          const endpoint = isLoginMode ? '/api/login' : '/api/register';
          
          // Send data to server
          fetch(endpoint, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                  username: username,
                  password: password
              }),
          })
          .then(response => response.json())
          .then(data => {
              if (data.success) {
                  if (isLoginMode) {
                      showMessage('Login successful! Redirecting...', 'success');
                  } else {
                      showMessage('Registration successful! You can now log in.', 'success');
                      // Switch back to login mode
                      isLoginMode = true;
                      formTitle.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
                      submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
                      toggleBtn.textContent = 'New player? Register here';
                      // Clear form
                      document.getElementById('username').value = '';
                      document.getElementById('password').value = '';
                      return;
                  }
                  // Redirect to home page after login
                  setTimeout(function() {
                      window.location.href = '/';
                  }, 1500);
              } else {
                  showMessage(data.message || 'Error processing request', 'error');
              }
          })
          .catch(error => {
              console.error('Error:', error);
              showMessage('Server error. Please try again later.', 'error');
          });
      });
  }
  
  // Function to show message to user
  function showMessage(text, type) {
      // Check if message container exists, if not create it
      let messageContainer = document.querySelector('.message-container');
      
      if (!messageContainer) {
          messageContainer = document.createElement('div');
          messageContainer.className = 'message-container';
          authForm.insertAdjacentElement('beforebegin', messageContainer);
      }
      
      // Create message element
      const message = document.createElement('div');
      message.className = `message ${type}`;
      message.textContent = text;
      
      // Add to container
      messageContainer.innerHTML = '';
      messageContainer.appendChild(message);
      
      // Auto remove after delay
      setTimeout(() => {
          message.classList.add('fade-out');
          setTimeout(() => {
              messageContainer.innerHTML = '';
          }, 500);
      }, 3000);
  }
  
  // Add these styles for messages
  const style = document.createElement('style');
  style.textContent = `
      .message-container {
          margin-bottom: 15px;
      }
      
      .message {
          padding: 10px 15px;
          border-radius: 5px;
          color: white;
          margin-bottom: 10px;
          animation: fadeIn 0.3s ease-in-out;
      }
      
      .message.success {
          background-color: rgba(76, 175, 80, 0.8);
      }
      
      .message.error {
          background-color: rgba(244, 67, 54, 0.8);
      }
      
      .message.fade-out {
          opacity: 0;
          transition: opacity 0.5s ease-in-out;
      }
  `;
  document.head.appendChild(style);
  });