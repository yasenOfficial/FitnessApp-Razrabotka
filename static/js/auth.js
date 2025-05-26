// static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
  const form       = document.getElementById('auth-form');
  const waitingDiv = document.getElementById('waiting-confirmation');

  // Error handling function
  function showMessage(message, type = 'error') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-toast ${type}`;
    messageDiv.innerHTML = `
      <div class="message-content">
        <span class="message-text">${message}</span>
        <button class="close-btn">&times;</button>
      </div>
    `;
    document.body.appendChild(messageDiv);

    // Add close button functionality
    const closeBtn = messageDiv.querySelector('.close-btn');
    closeBtn.addEventListener('click', () => messageDiv.remove());

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (document.body.contains(messageDiv)) {
        messageDiv.remove();
      }
    }, 5000);
  }

  // Add message toast styles
  const style = document.createElement('style');
  style.textContent = `
    .message-toast {
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 1000;
      animation: slideIn 0.3s ease-out;
    }

    .message-content {
      padding: 1rem 2rem;
      border-radius: 4px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
      display: flex;
      align-items: center;
      gap: 1rem;
      color: white;
    }

    .message-toast.error .message-content {
      background-color: #ff4757;
    }

    .message-toast.success .message-content {
      background-color: #2ed573;
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

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const username = form.querySelector('#username').value.trim();
    const password = form.querySelector('#password').value.trim();
    const emailEl = form.querySelector('#email');
    const isRegistration = emailEl && getComputedStyle(emailEl.parentElement).display !== 'none';
    const email = isRegistration ? emailEl.value.trim() : null;

    if (!username || !password || (isRegistration && !email)) {
      showMessage('Please fill in all fields', 'error');
      return;
    }

    const endpoint = isRegistration ? '/auth/api/register' : '/auth/api/login';
    const payload = { username, password };
    if (isRegistration) payload.email = email;

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const contentType = response.headers.get('content-type');
      const isJson = contentType && contentType.includes('application/json');
      const data = isJson ? await response.json() : null;

      if (!response.ok) {
        throw new Error(data?.message || 'Authentication failed');
      }

      if (isRegistration) {
        form.style.display = 'none';
        waitingDiv.style.display = 'block';
        showMessage('Registration successful! Please check your email.', 'success');
      } else {
        showMessage('Login successful! Redirecting...', 'success');
        setTimeout(() => window.location.href = '/profile', 800);
      }
    } catch (error) {
      showMessage(error.message, 'error');
    }
  });
});
