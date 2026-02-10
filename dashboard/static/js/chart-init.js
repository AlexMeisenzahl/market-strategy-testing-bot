/**
 * P&L Chart Initialization
 * 
 * Initializes and updates the P&L chart on the dashboard
 */

// Initialize P&L Chart
function initPnLChart() {
    const ctx = document.getElementById('pnlChart');
    if (!ctx) {
        console.log('P&L chart canvas not found');
        return;
    }
    
    fetch('/api/chart/pnl')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error('Error loading P&L chart:', data.error);
                ctx.parentElement.innerHTML = '<p class="text-gray-500">Chart data unavailable</p>';
                return;
            }

            const labels = data.labels || [];
            const values = data.values || [];

            // Determine color based on final value
            const finalValue = values.length > 0 ? values[values.length - 1] : 0;
            const isPositive = finalValue >= 0;
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'P&L',
                        data: values,
                        borderColor: isPositive ? '#10b981' : '#ef4444',
                        backgroundColor: isPositive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (context) => `$${context.parsed.y.toLocaleString()}`
                            }
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: (value) => `$${value.toLocaleString()}`
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading P&L chart:', error);
            if (ctx && ctx.parentElement) {
                ctx.parentElement.innerHTML = '<p class="text-gray-500">Chart data unavailable</p>';
            }
        });
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPnLChart);
} else {
    initPnLChart();
}
