document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initScrollReveal();
    initPasswordToggle();
    initSidebarToggle();
    initAutoCloseAlerts();
    initGlobalChatBadges();
});

/* ============================================================
   Theme Toggle (Dark Mode)
   ============================================================ */

function initThemeToggle() {
    // Apply saved theme immediately (before DOM paint)
    const saved = localStorage.getItem('pv-theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
    }

    updateThemeIcon();

    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';

        document.documentElement.setAttribute('data-theme', next);
        localStorage.setItem('pv-theme', next);
        updateThemeIcon();

        // Persist to server (if authenticated)
        const csrfEl = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        let csrfToken = null;

        if (csrfEl) {
            csrfToken = csrfEl.value;
        } else if (csrfMeta) {
            csrfToken = csrfMeta.getAttribute('content');
        } else {
            // Try to get from cookie
            csrfToken = getCookie('csrftoken');
        }

        if (csrfToken) {
            fetch('/api/theme/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
            }).catch(() => {}); // Silent fail — localStorage is the primary storage
        }
    });
}

function updateThemeIcon() {
    const icon = document.getElementById('themeIcon');
    if (!icon) return;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    icon.className = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-fill';
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function initScrollReveal() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
        document.querySelectorAll('.reveal-item').forEach(el => {
            el.classList.add('revealed');
        });
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = getComputedStyle(entry.target).getPropertyValue('--delay');
                if (delay) {
                    const delayNum = parseFloat(delay);
                    const cappedDelay = Math.min(delayNum * 70, 500);
                    entry.target.style.transitionDelay = cappedDelay + 'ms';
                }
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.08,
        rootMargin: '0px 0px -40px 0px'
    });

    document.querySelectorAll('.reveal-item').forEach(el => {
        observer.observe(el);
    });
}

function initPasswordToggle() {
    const toggle = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('id_password');

    if (toggle && passwordInput) {
        toggle.addEventListener('click', () => {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            const icon = toggle.querySelector('i');
            icon.classList.toggle('bi-eye');
            icon.classList.toggle('bi-eye-slash');
        });
    }
}

function initSidebarToggle() {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebarToggle');
    const overlay = document.getElementById('sidebarOverlay');

    if (!sidebar || !toggleBtn) return;

    function openSidebar() {
        sidebar.classList.add('open');
        if (overlay) overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    toggleBtn.addEventListener('click', () => {
        if (sidebar.classList.contains('open')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });
}

function initAutoCloseAlerts() {
    document.querySelectorAll('.pv-alert').forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
}

function initGlobalChatBadges() {
    // Only poll if logged in (check for logout link as a proxy)
    const isLoggedIn = !!document.querySelector('a[href="/logout/"]');
    if (!isLoggedIn) return;

    // Check every 15 seconds
    setInterval(updateChatBadges, 15000);
    // Also check once immediately
    setTimeout(updateChatBadges, 1000);
}

function updateChatBadges() {
    // Don't poll if we're on the chat page (it has its own engine)
    if (window.location.pathname.includes('/chat/')) return;

    fetch('/chat/api/rooms/', {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(r => r.json())
    .then(data => {
        if (!data.rooms) return;
        const totalUnread = data.rooms.reduce((acc, room) => acc + room.unread_count, 0);
        
        // Update sidebar badge
        const sidebarBadge = document.querySelector('.pv-sidebar-chat-badge');
        if (sidebarBadge) {
            if (totalUnread > 0) {
                sidebarBadge.textContent = totalUnread;
                sidebarBadge.style.display = 'inline-flex';
            } else {
                sidebarBadge.style.display = 'none';
            }
        }

        // Update topbar/navbar dot
        const navDots = document.querySelectorAll('#globalChatDot');
        navDots.forEach(dot => {
            dot.style.display = totalUnread > 0 ? 'block' : 'none';
        });
    })
    .catch(() => {});
}
