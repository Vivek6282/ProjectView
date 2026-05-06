(function() {
    if (!window.PV_CONFIG || window.PV_CONFIG.hasSeenTutorial) return;

    const role = window.PV_CONFIG.userRole || 'employee';
    const tutorials = {
        employee: [
            { title: "Welcome, Team Member", text: "Use the Chat icon in the top right to coordinate with managers and HR instantly." },
            { title: "Project Tracking", text: "Monitor your deadlines and progress in the Projects workspace. Everything is live." }
        ],
        manager: [
            { title: "Hello, Manager", text: "You can now delete group chats you've created. Look for the 'Delete Group' button in Group Info." },
            { title: "Urgent Nudges", text: "Send direct priority alerts to employees from the User Administration registry." }
        ],
        hr: [
            { title: "HR Administration", text: "Manage the local account registry and monitor user activity from the Admin Portal." },
            { title: "Group Management", text: "You have full authority to delete group chats you've initiated to keep communication clean." }
        ]
    };

    const steps = tutorials[role] || tutorials.employee;
    let currentStep = 0;

    const overlay = document.createElement('div');
    overlay.className = 'pv-tutorial-overlay';
    overlay.style.display = 'flex';
    
    function renderStep() {
        const step = steps[currentStep];
        overlay.innerHTML = `
            <div class="pv-tutorial-card text-center">
                <div class="pv-overline mb-2">Step ${currentStep + 1} of ${steps.length}</div>
                <h2 class="fw-bold mb-3">${step.title}</h2>
                <p class="text-muted-custom mb-5 fs-5">${step.text}</p>
                <div class="d-flex justify-content-center gap-3">
                    ${currentStep < steps.length - 1 
                        ? `<button class="btn pv-btn-primary px-5 py-2" id="pv-tut-next">Next</button>`
                        : `<button class="btn pv-btn-primary px-5 py-2" id="pv-tut-finish">Finish Guide</button>`
                    }
                </div>
            </div>
        `;

        const nextBtn = document.getElementById('pv-tut-next');
        const finishBtn = document.getElementById('pv-tut-finish');

        if (nextBtn) {
            nextBtn.onclick = () => {
                currentStep++;
                renderStep();
            };
        }
        if (finishBtn) {
            finishBtn.onclick = () => finishTutorial();
        }
    }

    function finishTutorial() {
        const formData = new FormData();
        formData.append('flag', 'has_seen_tutorial');
        
        fetch('/api/profile/flag/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': window.PV_CONFIG.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        }).then(() => {
            overlay.remove();
        });
    }

    document.body.appendChild(overlay);
    renderStep();
})();
