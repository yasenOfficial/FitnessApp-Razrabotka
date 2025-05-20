// static/js/profile.js
document.addEventListener('DOMContentLoaded',function(){
  // Logout
  document.getElementById('logout-btn')?.addEventListener('click',e=>{
    e.preventDefault();
    fetch('/api/logout',{method:'POST'}).then(_=>window.location.href='/');
  });
  // Delete Account
  document.getElementById('delete-profile')?.addEventListener('click',()=>{
    if(confirm('Delete your account?')) {
      fetch('/api/delete',{method:'DELETE'})
        .then(r=>r.json())
        .then(d=>{
          if(d.success) window.location.href='/';
          else alert(d.message);
        });
    }
  });
});
