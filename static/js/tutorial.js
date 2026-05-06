(function() {
    function startTutorial(manual = false) {
        if (!window.PV_CONFIG) return;
        if (!manual && window.PV_CONFIG.hasSeenTutorial) return;

        const role = window.PV_CONFIG.userRole || 'employee';
        const tutorials = {
            employee: [
                { title: "Welcome, Team Member", text: "Use the Chat icon in the top right to coordinate with managers and HR instantly." },
                { title: "Project Workspace", text: "Monitor your assigned projects and deadlines in real-time. Everything is modular and live." },
                { title: "Private Messaging", text: "Start a Direct Message with any colleague by clicking 'Chat' next to their name in the user list." },
                { title: "Visual Comfort", text: "Use the Moon/Sun icon in the top bar to toggle between Light and Dark themes anytime." }
            ],
            manager: [
                { title: "Hello, Manager", text: "You have full control over the groups you create. Use 'Delete Group' in the header to clean up old chats." },
                { title: "Urgent Nudges", text: "Need immediate attention? Send high-priority priority nudges to employees from the Users registry." },
                { title: "Performance Analytics", text: "Monitor completion velocity and administrator workload directly from your dashboard." },
                { title: "Team Management", text: "Keep your workspace secure by activating or deactivating user accounts as needed." }
            ],
            hr: [
                { title: "HR Administration", text: "As an HR Manager, you oversee the local account registry and monitor all user activity." },
                { title: "Onboarding Users", text: "Register new team members and assign their roles directly from the 'Register New User' portal." },
                { title: "Group Moderation", text: "You can delete any group chat you initiated to maintain professional communication standards." },
                { title: "Global Communication", text: "Use the Urgent Nudge feature to ensure your critical messages are seen and acknowledged instantly." }
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
                    <div class="pv-overline mb-2">Guide: ${currentStep + 1} of ${steps.length}</div>
                    <h2 class="fw-bold mb-3">${step.title}</h2>
                    <p class="text-muted-custom mb-5 fs-5">${step.text}</p>
                    <div class="d-flex justify-content-center gap-3">
                        ${currentStep > 0 ? `<button class="btn pv-btn-outline px-4 py-2" id="pv-tut-prev">Back</button>` : ''}
                        ${currentStep < steps.length - 1 
                            ? `<button class="btn pv-btn-primary px-5 py-2" id="pv-tut-next">Next Step</button>`
                            : `<button class="btn pv-btn-primary px-5 py-2" id="pv-tut-finish">Finish Journey</button>`
                        }
                    </div>
                </div>
            `;

            const nextBtn = document.getElementById('pv-tut-next');
            const prevBtn = document.getElementById('pv-tut-prev');
            const finishBtn = document.getElementById('pv-tut-finish');

            if (nextBtn) {
                nextBtn.onclick = () => {
                    currentStep++;
                    renderStep();
                };
            }
            if (prevBtn) {
                prevBtn.onclick = () => {
                    currentStep--;
                    renderStep();
                };
            }
            if (finishBtn) {
                finishBtn.onclick = () => finishTutorial();
            }
        }

        function finishTutorial() {
            if (!manual) {
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
            } else {
                overlay.remove();
            }
        }

        document.body.appendChild(overlay);
        renderStep();
    }

    // Export to window
    window.startTutorial = () => startTutorial(true);

    // Auto-start if needed
    document.addEventListener('DOMContentLoaded', () => {
        if (window.PV_CONFIG && !window.PV_CONFIG.hasSeenTutorial) {
            setTimeout(() => startTutorial(false), 800);
        }
    });
})();
