// static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
  const form       = document.getElementById('auth-form');
  const showMessage= window.showMessage || ((txt, t)=>alert(txt));
  const waitingDiv = document.getElementById('waiting-confirmation');

  form.addEventListener('submit', async e => {
    e.preventDefault();
    const u = form.querySelector('#username').value.trim();
    const p = form.querySelector('#password').value.trim();
    const emailEl = form.querySelector('#email');
    const isReg = emailEl && getComputedStyle(emailEl.parentElement).display!=='none';
    const mailVal= isReg ? emailEl.value.trim() : null;

    if (!u||!p||(isReg&&!mailVal)) {
      return showMessage('Please fill in all fields', 'error');
    }

    const ep  = isReg ? '/api/register' : '/api/login';
    const pd  = { username:u, password:p };
    if(isReg) pd.email = mailVal;

    try {
      const res = await fetch(ep, {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(pd)
      });
      const body = await res.json();
      if (!body.success) {
        throw new Error(body.message||'Error');
      }
      if (isReg) {
        form.style.display='none';
        waitingDiv.style.display='block';
      } else {
        showMessage('Login successful! Redirecting…','success');
        setTimeout(()=>window.location.href='/profile',800);
      }
    } catch(err) {
      showMessage(err.message,'error');
    }
  });
});
