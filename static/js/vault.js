/* Wault — client-side interactions */

// ── MOBILE DRAWER ──
(function () {
  const toggle  = document.getElementById('menuToggle');
  const drawer  = document.getElementById('mobileDrawer');
  const overlay = document.getElementById('mobileOverlay');
  const closeBtn = document.getElementById('drawerClose');
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');

  function openDrawer() {
    drawer && drawer.classList.add('open');
    overlay && overlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeDrawer() {
    drawer && drawer.classList.remove('open');
    overlay && overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  toggle && toggle.addEventListener('click', openDrawer);
  mobileMenuBtn && mobileMenuBtn.addEventListener('click', openDrawer);
  closeBtn && closeBtn.addEventListener('click', closeDrawer);
  overlay && overlay.addEventListener('click', closeDrawer);
})();

// ── AUTO-DISMISS TOASTS ──
(function () {
  const toasts = document.querySelectorAll('.toast');
  toasts.forEach(function (toast) {
    setTimeout(function () {
      toast.style.transition = 'opacity 0.4s';
      toast.style.opacity = '0';
      setTimeout(function () { toast.remove(); }, 400);
    }, 4000);
  });
})();

// ── SEARCH AUTO-SUBMIT (with debounce) ──
(function () {
  const searchInput = document.querySelector('.search-bar input[name="q"]');
  if (!searchInput) return;
  let timer;
  searchInput.addEventListener('input', function () {
    clearTimeout(timer);
    // Only auto-submit if 3+ chars or cleared
    if (this.value.length >= 3 || this.value.length === 0) {
      timer = setTimeout(function () {
        searchInput.closest('form').submit();
      }, 500);
    }
  });
})();
