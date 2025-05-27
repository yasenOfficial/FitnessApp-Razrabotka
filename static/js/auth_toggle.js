document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-btn');
  const formTitle = document.getElementById('form-title');
  const submitBtn = document.getElementById('submit-btn');
  const emailGroup = document.getElementById('email-group');
  let isLogin = true;

  console.log('Auth toggle script loaded');
  console.log('Elements found:', {
    toggleBtn: !!toggleBtn,
    formTitle: !!formTitle,
    submitBtn: !!submitBtn,
    emailGroup: !!emailGroup
  });

  if (!toggleBtn || !formTitle || !submitBtn || !emailGroup) {
    console.error('Some required elements are missing');
    return;
  }

  toggleBtn.addEventListener('click', () => {
    console.log('Toggle button clicked, switching to:', isLogin ? 'register' : 'login');
    isLogin = !isLogin;
    if (isLogin) {
      formTitle.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
      submitBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
      toggleBtn.textContent = 'New player? Register here';
      emailGroup.style.display = 'none';
    } else {
      formTitle.innerHTML = '<i class="fas fa-user-plus"></i> Register';
      submitBtn.innerHTML = '<i class="fas fa-user-plus"></i> Register';
      toggleBtn.textContent = 'Already have an account? Login';
      emailGroup.style.display = 'block';
    }
  });
});