const PV_COLORS = {
    accent: '#5C6B4F',
    accentLight: '#6B7F5E',
    red: '#C0392B',
    orange: '#D4790E',
    green: '#27AE60',
    blue: '#2C82C9',
    purple: '#8E44AD',
    teal: '#16A085',
    navy: '#2C3E50',
    grey: '#95A5A6',
};

const PALETTE = [
    PV_COLORS.accent, PV_COLORS.blue, PV_COLORS.orange, PV_COLORS.green,
    PV_COLORS.red, PV_COLORS.purple, PV_COLORS.teal, PV_COLORS.navy,
    PV_COLORS.grey, PV_COLORS.accentLight
];

const CHART_DEFAULTS = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                font: { family: "'Inter', sans-serif", size: 12, weight: '500' },
                padding: 16,
                usePointStyle: true,
                pointStyleWidth: 8,
            }
        },
        tooltip: {
            backgroundColor: '#1A1A1A',
            titleFont: { family: "'Inter', sans-serif", weight: '600' },
            bodyFont: { family: "'Inter', sans-serif" },
            cornerRadius: 8,
            padding: 10,
        }
    },
    scales: {
        x: {
            grid: { display: false },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } }
        },
        y: {
            grid: { color: 'rgba(0,0,0,0.04)' },
            ticks: { font: { family: "'Inter', sans-serif", size: 11 } },
            beginAtZero: true,
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    fetch('/dashboard/analytics.json')
        .then(res => res.json())
        .then(data => {
            renderVelocityChart(data.velocity);
            renderStatusMatrixChart(data.prio_status);
            renderTimelineChart(data.deadlines_30);
            renderUserWorkloadChart(data.by_user);
            renderCategoryChart(data.by_category);
            renderPriorityChart(data.by_priority);
            renderStatusChart(data.by_status);
            renderOverdueTrend(data.overdue_trend);
        })
        .catch(err => console.error('Chart data fetch failed:', err));
});

function renderVelocityChart(data) {
    const ctx = document.getElementById('chartVelocity');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.month),
            datasets: [{
                label: 'Projects Completed',
                data: data.map(d => d.count),
                backgroundColor: PV_COLORS.accent,
                borderRadius: 4,
                borderSkipped: false,
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: { display: false }
            }
        }
    });
}

function renderStatusMatrixChart(data) {
    const ctx = document.getElementById('chartStatusMatrix');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.priority),
            datasets: [
                {
                    label: 'Planned',
                    data: data.map(d => d.Planned),
                    backgroundColor: PV_COLORS.blue,
                },
                {
                    label: 'In Progress',
                    data: data.map(d => d['In Progress']),
                    backgroundColor: PV_COLORS.orange,
                },
                {
                    label: 'Done',
                    data: data.map(d => d.Done),
                    backgroundColor: PV_COLORS.green,
                }
            ]
        },
        options: {
            ...CHART_DEFAULTS,
            indexAxis: 'y',
            scales: {
                x: { stacked: true, ...CHART_DEFAULTS.scales.x },
                y: { stacked: true, ...CHART_DEFAULTS.scales.y }
            },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderUserWorkloadChart(data) {
    const ctx = document.getElementById('chartUserWorkload');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.created_by__username || 'System'),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: PALETTE,
                borderWidth: 0,
                spacing: 2,
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            cutout: '70%',
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderTimelineChart(data) {
    const ctx = document.getElementById('chartTimeline');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => {
                const dt = new Date(d.deadline);
                return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [{
                label: 'Project Deadlines',
                data: data.map(d => d.count),
                borderColor: PV_COLORS.accent,
                backgroundColor: 'rgba(92,107,79,0.08)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: { display: false }
            }
        }
    });
}

function renderCategoryChart(data) {
    const ctx = document.getElementById('chartCategory');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.category),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: PALETTE,
                borderRadius: 4,
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            indexAxis: 'y',
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: { display: false }
            }
        }
    });
}

function renderPriorityChart(data) {
    const ctx = document.getElementById('chartPriority');
    if (!ctx) return;
    const colors = { 'Low': PV_COLORS.green, 'Medium': PV_COLORS.orange, 'High': PV_COLORS.red };
    new Chart(ctx, {
        type: 'polarArea',
        data: {
            labels: data.map(d => d.priority),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: data.map(d => colors[d.priority] || PV_COLORS.grey),
                borderWidth: 0,
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            scales: { r: { ticks: { display: false } } },
            plugins: {
                ...CHART_DEFAULTS.plugins,
                legend: { position: 'bottom' }
            }
        }
    });
}

function renderStatusChart(data) {
    const ctx = document.getElementById('chartStatus');
    if (!ctx) return;
    const colors = { 'Planned': PV_COLORS.blue, 'In Progress': PV_COLORS.orange, 'Done': PV_COLORS.green };
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.status),
            datasets: [{
                data: data.map(d => d.count),
                backgroundColor: data.map(d => colors[d.status] || PV_COLORS.grey),
                borderWidth: 0,
                spacing: 2,
            }]
        },
        options: {
            ...CHART_DEFAULTS,
            cutout: '65%',
            plugins: { ...CHART_DEFAULTS.plugins, legend: { position: 'right' } }
        }
    });
}

function renderOverdueTrend(data) {
    const ctx = document.getElementById('chartOverdueTrend');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.map(d => {
                const dt = new Date(d.week);
                return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            }),
            datasets: [{
                label: 'Overdue Projects',
                data: data.map(d => d.count),
                borderColor: PV_COLORS.red,
                backgroundColor: 'rgba(192,57,43,0.05)',
                fill: true,
                tension: 0.3,
            }]
        },
        options: CHART_DEFAULTS
    });
}
