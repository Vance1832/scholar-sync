// Flash message auto-dismiss
document.querySelectorAll('.flash').forEach(function (el) {
  var closeBtn = el.querySelector('.flash-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', function () { el.remove(); });
  }
  setTimeout(function () {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(function () { el.remove(); }, 400);
  }, 4000);
});

// Role tab switcher on auth pages
var roleTabs = document.querySelectorAll('.role-tab');
var roleInput = document.getElementById('role-input');

roleTabs.forEach(function (tab) {
  tab.addEventListener('click', function () {
    roleTabs.forEach(function (t) { t.classList.remove('active'); });
    tab.classList.add('active');
    if (roleInput) { roleInput.value = tab.dataset.role; }
  });
});

// Confirm dialogs for destructive actions
document.querySelectorAll('[data-confirm]').forEach(function (el) {
  el.addEventListener('click', function (e) {
    if (!window.confirm(el.dataset.confirm)) { e.preventDefault(); }
  });
});

// Submit form on behalf of btn (for method-override buttons)
document.querySelectorAll('button[form]').forEach(function (btn) {
  // native behavior is fine; just ensure no double-submit
});
