/**
 * Charts Initialization - Initialize All Dashboard Charts
 * 
 * Handles initialization and updating of all Chart.js charts on dashboard pages.
 */

// Chart instances cache
const chartInstances = {};

/**
 * Initialize all charts on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check which charts exist on the page and initialize them
    if (document.getElementById('pnlChart')) {
        initPnLChart();
    }
    if (document.getElementById('allocationChart')) {
        initAllocationChart();
    }
    if (document.getElementById('distributionChart')) {
        initDistributionChart();
    }
    if (document.getElementById('cumulativeChart')) {
        initCumulativeChart();
    }
    if (document.getElementById('strategyComparisonChart')) {
        initStrategyComparisonChart();
    }
});

/**
 * Initialize P&L Chart
 */
function initPnLChart() {
    const ctx = document.getElementById('pnlChart');
    if (!ctx) return;
    
    fetch('/api/chart/cumulative')
        .then(r => r.json())
        .then(data => {
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => new Date(d.date).toLocaleDateString()),
                    datasets: [{
                        label: 'P&L',
                        data: data.map(d => d.value),
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            chartInstances['pnl'] = chart;
        })
        .catch(error => {
            console.error('Error loading P&L chart:', error);
            showChartError(ctx, 'Failed to load P&L data');
        });
}

/**
 * Initialize Allocation Chart (Pie)
 */
function initAllocationChart() {
    const ctx = document.getElementById('allocationChart');
    if (!ctx) return;
    
    fetch('/api/chart/allocation')
        .then(r => r.json())
        .then(data => {
            const chart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        data: data.data || [],
                        backgroundColor: [
                            'rgb(255, 99, 132)',
                            'rgb(54, 162, 235)',
                            'rgb(255, 205, 86)',
                            'rgb(75, 192, 192)',
                            'rgb(153, 102, 255)',
                            'rgb(255, 159, 64)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.parsed || 0;
                                    return label + ': $' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            chartInstances['allocation'] = chart;
        })
        .catch(error => {
            console.error('Error loading allocation chart:', error);
            showChartError(ctx, 'Failed to load allocation data');
        });
}

/**
 * Initialize Distribution Chart (Bar)
 */
function initDistributionChart() {
    const ctx = document.getElementById('distributionChart');
    if (!ctx) return;
    
    fetch('/api/chart/distribution')
        .then(r => r.json())
        .then(data => {
            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels || ['Wins', 'Losses'],
                    datasets: [{
                        label: 'Trades',
                        data: data.data || [0, 0],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(255, 99, 132, 0.8)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
            chartInstances['distribution'] = chart;
        })
        .catch(error => {
            console.error('Error loading distribution chart:', error);
            showChartError(ctx, 'Failed to load distribution data');
        });
}

/**
 * Initialize Cumulative Returns Chart
 */
function initCumulativeChart() {
    const ctx = document.getElementById('cumulativeChart');
    if (!ctx) return;
    
    fetch('/api/chart/cumulative')
        .then(r => r.json())
        .then(data => {
            const chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map(d => new Date(d.date).toLocaleDateString()),
                    datasets: [{
                        label: 'Cumulative Returns',
                        data: data.map(d => d.value),
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.1,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            chartInstances['cumulative'] = chart;
        })
        .catch(error => {
            console.error('Error loading cumulative chart:', error);
            showChartError(ctx, 'Failed to load cumulative data');
        });
}

/**
 * Initialize Strategy Comparison Chart
 */
function initStrategyComparisonChart() {
    const ctx = document.getElementById('strategyComparisonChart');
    if (!ctx) return;
    
    fetch('/api/strategies/performance')
        .then(r => r.json())
        .then(data => {
            const strategies = data.strategies || [];
            const chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: strategies.map(s => s.name),
                    datasets: [{
                        label: 'Total P&L',
                        data: strategies.map(s => s.total_pnl || 0),
                        backgroundColor: strategies.map(s => 
                            s.total_pnl >= 0 ? 'rgba(75, 192, 192, 0.8)' : 'rgba(255, 99, 132, 0.8)'
                        )
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    }
                }
            });
            chartInstances['strategyComparison'] = chart;
        })
        .catch(error => {
            console.error('Error loading strategy comparison chart:', error);
            showChartError(ctx, 'Failed to load strategy data');
        });
}

/**
 * Show error message on chart canvas
 */
function showChartError(ctx, message) {
    const parent = ctx.parentElement;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'chart-error';
    errorDiv.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <p>${message}</p>
    `;
    errorDiv.style.cssText = `
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 300px;
        color: #e74c3c;
    `;
    parent.appendChild(errorDiv);
    ctx.style.display = 'none';
}

/**
 * Update chart data (for real-time updates)
 */
function updateChart(chartName, newData) {
    const chart = chartInstances[chartName];
    if (!chart) return;
    
    // Update chart data
    chart.data = newData;
    chart.update();
}

/**
 * Destroy all charts (for cleanup)
 */
function destroyAllCharts() {
    Object.values(chartInstances).forEach(chart => {
        if (chart) chart.destroy();
    });
}
