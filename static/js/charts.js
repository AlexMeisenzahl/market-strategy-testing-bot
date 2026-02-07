// Charts.js - Chart rendering and management

let pnlChart = null;
let strategyChart = null;

// Load all charts
function loadCharts() {
    loadPnLChart();
    loadStrategyChart();
}

// Load P&L over time chart
async function loadPnLChart() {
    try {
        const response = await fetch('/api/chart/pnl');
        const data = await response.json();
        
        renderPnLChart(data.data);
    } catch (error) {
        console.error('Error loading P&L chart:', error);
    }
}

// Load strategy comparison chart
async function loadStrategyChart() {
    try {
        const response = await fetch('/api/chart/strategies');
        const data = await response.json();
        
        renderStrategyChart(data);
    } catch (error) {
        console.error('Error loading strategy chart:', error);
    }
}

// Render P&L chart
function renderPnLChart(data) {
    const canvas = document.getElementById('pnl-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (pnlChart) {
        pnlChart.destroy();
    }
    
    // Prepare data
    const labels = data.map(d => new Date(d.timestamp).toLocaleTimeString());
    const values = data.map(d => d.pnl);
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(46, 204, 113, 0.5)');
    gradient.addColorStop(1, 'rgba(46, 204, 113, 0.0)');
    
    pnlChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cumulative P&L',
                data: values,
                borderColor: '#2ecc71',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#2ecc71',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#ffffff',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#2ecc71',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return 'P&L: $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#b0b0b0',
                        maxTicksLimit: 10
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#b0b0b0',
                        callback: function(value) {
                            return '$' + value.toFixed(2);
                        }
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Render strategy comparison chart
function renderStrategyChart(data) {
    const canvas = document.getElementById('strategy-chart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if it exists
    if (strategyChart) {
        strategyChart.destroy();
    }
    
    // Determine which data to show based on currentChartView
    const values = currentChartView === 'pnl' ? data.pnl : data.win_rates;
    const label = currentChartView === 'pnl' ? 'Total P&L ($)' : 'Win Rate (%)';
    
    // Color bars based on values
    const backgroundColors = values.map(v => {
        if (currentChartView === 'pnl') {
            return v >= 0 ? 'rgba(46, 204, 113, 0.8)' : 'rgba(231, 76, 60, 0.8)';
        } else {
            return v >= 50 ? 'rgba(46, 204, 113, 0.8)' : 'rgba(243, 156, 18, 0.8)';
        }
    });
    
    const borderColors = values.map(v => {
        if (currentChartView === 'pnl') {
            return v >= 0 ? '#2ecc71' : '#e74c3c';
        } else {
            return v >= 50 ? '#2ecc71' : '#f39c12';
        }
    });
    
    strategyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: label,
                data: values,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#ffffff',
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#3498db',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            if (currentChartView === 'pnl') {
                                return label + ': $' + context.parsed.y.toFixed(2);
                            } else {
                                return label + ': ' + context.parsed.y.toFixed(1) + '%';
                            }
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                    },
                    ticks: {
                        color: '#b0b0b0',
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false,
                    },
                    ticks: {
                        color: '#b0b0b0',
                        callback: function(value) {
                            if (currentChartView === 'pnl') {
                                return '$' + value.toFixed(2);
                            } else {
                                return value.toFixed(0) + '%';
                            }
                        }
                    }
                }
            }
        }
    });
}

// Toggle chart view between P&L and Win Rate
function toggleChartView(view) {
    currentChartView = view;
    
    // Update toggle button states
    document.querySelectorAll('.btn-toggle').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Reload strategy chart with new view
    loadStrategyChart();
}
