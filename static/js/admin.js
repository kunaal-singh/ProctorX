/**
 * Admin JavaScript — chart rendering and admin utilities.
 */

function renderViolationTypeChart(data) {
    const ctx = document.getElementById('violationTypeChart');
    if (!ctx) return;

    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = [
        '#6C5CE7', '#00B894', '#D63031', '#FDCB6E', '#0984E3',
        '#E17055', '#00CEC9', '#FD79A8', '#636E72', '#2D3436'
    ];

    new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 0,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#ccc',
                        padding: 12,
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

// Confirm delete action
function confirmDelete(name) {
    return confirm(`Are you sure you want to delete student "${name}"? This action cannot be undone.`);
}
