(function() {
    if (sessionStorage.getItem('pv_welcome_seen')) return;

    const overlay = document.createElement('div');
    overlay.className = 'pv-cinema-welcome';
    overlay.innerHTML = `
        <div class="pv-cinema-text">
            Project View<br>
            <span style="color: var(--pv-accent); font-size: 0.5em; opacity: 0.8; letter-spacing: 0.5em;">Excellence Redefined</span>
        </div>
    `;
    document.body.appendChild(overlay);

    // Trigger animation
    requestAnimationFrame(() => {
        overlay.classList.add('active');
    });

    setTimeout(() => {
        overlay.classList.remove('active');
        sessionStorage.setItem('pv_welcome_seen', 'true');
        setTimeout(() => overlay.remove(), 800);
    }, 3500);
})();
