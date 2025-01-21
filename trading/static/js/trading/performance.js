// static/js/trading/performance.js
class PerformanceAnalyzer {
    constructor() {
        this.charts = {};
        this.filters = {
            dateRange: '30',
            strategy: '',
            symbol: ''
        };
        this.initializeCharts();
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Filter form
        document.getElementById('analysisFilterForm')?.addEventListener('submit', 
            this.handleFilterSubmit.bind(this));

        // Date range selector
        document.getElementById('dateRange')?.addEventListener('change',
            this.handleDateRangeChange.bind(this));

        // Export data button
        document.getElementById('exportData')?.addEventListener('click',
            this.exportAnalysisData.bind(this));
    }

    async initializeCharts() {
        await this.createEquityChart();
        await this.createDrawdownChart();
        await this.createDistributionChart();
        await this.createTimeAnalysisChart();
    }

    async createEquityChart() {
        const ctx = document.getElementById('equityChart');
        if (!ctx) return;

        try {
            const data = await this.fetchEquityData();
            
            this.charts.equity = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: 'Equity',
                        data: data.equity,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    },
                    {
                        label: 'Balance',
                        data: data.balance,
                        borderColor: 'rgb(54, 162, 235)',
                        tension: 0.1,
                        borderDash: [5, 5]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Equity Curve'
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: $${context.raw.toFixed(2)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            title: {
                                display: true,
                                text: 'Value ($)'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating equity chart:', error);
        }
    }

    async createDrawdownChart() {
        const ctx = document.getElementById('drawdownChart');
        if (!ctx) return;

        try {
            const data = await this.fetchDrawdownData();

            this.charts.drawdown = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: 'Drawdown',
                        data: data.drawdown,
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        fill: true,
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Drawdown Analysis'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Drawdown: ${(context.raw * 100).toFixed(2)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            reverse: true,
                            title: {
                                display: true,
                                text: 'Drawdown (%)'
                            },
                            ticks: {
                                callback: function(value) {
                                    return `${(value * 100).toFixed(0)}%`;
                                }
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating drawdown chart:', error);
        }
    }

    async createDistributionChart() {
        const ctx = document.getElementById('distributionChart');
        if (!ctx) return;

        try {
            const data = await this.fetchTradeDistributionData();

            this.charts.distribution = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.ranges,
                    datasets: [{
                        label: 'Trade Distribution',
                        data: data.frequencies,
                        backgroundColor: data.frequencies.map(val => 
                            val >= 0 ? 'rgba(75, 192, 192, 0.5)' : 'rgba(255, 99, 132, 0.5)'
                        ),
                        borderColor: data.frequencies.map(val =>
                            val >= 0 ? 'rgb(75, 192, 192)' : 'rgb(255, 99, 132)'
                        ),
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Profit Distribution'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Trades: ${context.raw}`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Trades'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Profit Range ($)'
                            }
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating distribution chart:', error);
        }
    }

    async createTimeAnalysisChart() {
        const ctx = document.getElementById('timeAnalysisChart');
        if (!ctx) return;

        try {
            const data = await this.fetchTimeAnalysisData();

            this.charts.timeAnalysis = new Chart(ctx, {
                type: 'heatmap',
                data: {
                    datasets: [{
                        data: data.heatmap,
                        backgroundColor: function(context) {
                            const value = context.raw.v;
                            const alpha = (value + 1) / 2;
                            return value > 0 
                                ? `rgba(75, 192, 192, ${alpha})`
                                : `rgba(255, 99, 132, ${alpha})`;
                        }
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Trading Performance by Time'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.raw.v;
                                    return `Win Rate: ${(value * 100).toFixed(1)}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            type: 'category',
                            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                            offset: true
                        },
                        x: {
                            type: 'category',
                            labels: Array.from({length: 24}, (_, i) => i),
                            offset: true
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error creating time analysis chart:', error);
        }
    }

    async handleFilterSubmit(event) {
        event.preventDefault();
        await this.updateAnalysis();
    }

    async handleDateRangeChange(event) {
        const value = event.target.value;
        if (value === 'custom') {
            this.showCustomDatePicker();
        } else {
            this.filters.dateRange = value;
            await this.updateAnalysis();
        }
    }

    showCustomDatePicker() {
        // Implementation for custom date range picker
    }

    async updateAnalysis() {
        try {
            const data = await this.fetchAnalysisData();
            this.updateMetrics(data.metrics);
            this.updateCharts(data.charts);
            this.updateTradeTable(data.trades);
        } catch (error) {
            console.error('Error updating analysis:', error);
            this.showNotification('Error updating analysis', 'error');
        }
    }

    updateMetrics(metrics) {
        document.getElementById('totalProfit').textContent = 
            `$${metrics.total_profit.toFixed(2)}`;
        document.getElementById('winRate').textContent = 
            `${(metrics.win_rate * 100).toFixed(1)}%`;
        document.getElementById('profitFactor').textContent = 
            metrics.profit_factor.toFixed(2);
        document.getElementById('sharpeRatio').textContent = 
            metrics.sharpe_ratio.toFixed(2);
    }

    updateCharts(chartData) {
        Object.entries(this.charts).forEach(([chartName, chart]) => {
            if (chartData[chartName]) {
                chart.data = chartData[chartName];
                chart.update();
            }
        });
    }

    updateTradeTable(trades) {
        const tbody = document.getElementById('tradeAnalysisTable');
        if (!tbody) return;

        tbody.innerHTML = trades.map(trade => this.createTradeRow(trade)).join('');
    }

    createTradeRow(trade) {
        return `
            <tr>
                <td>${new Date(trade.open_time).toLocaleString()}</td>
                <td>${trade.symbol}</td>
                <td>
                    <span class="badge ${trade.type === 'BUY' ? 'bg-success' : 'bg-danger'}">
                        ${trade.type}
                    </span>
                </td>
                <td>${trade.entry_price}</td>
                <td>${trade.exit_price || '-'}</td>
                <td class="${trade.profit >= 0 ? 'text-success' : 'text-danger'}">
                    $${trade.profit.toFixed(2)}
                </td>
                <td>${trade.strategy}</td>
                <td>${trade.models_used}</td>
            </tr>
        `;
    }

    async exportAnalysisData() {
        try {
            const response = await fetch('/api/trading/export-analysis/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(this.filters)
            });

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'trading_analysis.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

        } catch (error) {
            console.error('Error exporting data:', error);
            this.showNotification('Error exporting data', 'error');
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    showNotification(message, type) {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}-toast`;
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Auto remove after shown
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }
    
    // API calls implementations
    async fetchEquityData() {
        try {
            const queryParams = new URLSearchParams({
                date_range: this.filters.dateRange,
                strategy: this.filters.strategy,
                symbol: this.filters.symbol
            });
    
            const response = await fetch(`/api/trading/analysis/equity/?${queryParams}`);
            if (!response.ok) throw new Error('Failed to fetch equity data');
            
            const data = await response.json();
            return {
                dates: data.map(d => new Date(d.date)),
                equity: data.map(d => d.equity),
                balance: data.map(d => d.balance)
            };
        } catch (error) {
            console.error('Error fetching equity data:', error);
            throw error;
        }
    }
    
    async fetchDrawdownData() {
        try {
            const queryParams = new URLSearchParams({
                date_range: this.filters.dateRange,
                strategy: this.filters.strategy,
                symbol: this.filters.symbol
            });
    
            const response = await fetch(`/api/trading/analysis/drawdown/?${queryParams}`);
            if (!response.ok) throw new Error('Failed to fetch drawdown data');
            
            const data = await response.json();
            return {
                dates: data.map(d => new Date(d.date)),
                drawdown: data.map(d => d.drawdown)
            };
        } catch (error) {
            console.error('Error fetching drawdown data:', error);
            throw error;
        }
    }
    
    async fetchTradeDistributionData() {
        try {
            const queryParams = new URLSearchParams({
                date_range: this.filters.dateRange,
                strategy: this.filters.strategy,
                symbol: this.filters.symbol
            });
    
            const response = await fetch(`/api/trading/analysis/distribution/?${queryParams}`);
            if (!response.ok) throw new Error('Failed to fetch distribution data');
            
            const data = await response.json();
            return {
                ranges: data.map(d => `$${d.range_start} to $${d.range_end}`),
                frequencies: data.map(d => d.count)
            };
        } catch (error) {
            console.error('Error fetching distribution data:', error);
            throw error;
        }
    }
    
    async fetchTimeAnalysisData() {
        try {
            const queryParams = new URLSearchParams({
                date_range: this.filters.dateRange,
                strategy: this.filters.strategy,
                symbol: this.filters.symbol
            });
    
            const response = await fetch(`/api/trading/analysis/time/?${queryParams}`);
            if (!response.ok) throw new Error('Failed to fetch time analysis data');
            
            const data = await response.json();
            
            // Transform data for heatmap
            const heatmap = [];
            for (let day = 0; day < 5; day++) {
                for (let hour = 0; hour < 24; hour++) {
                    const cellData = data.find(d => d.day === day && d.hour === hour);
                    if (cellData) {
                        heatmap.push({
                            x: hour,
                            y: day,
                            v: cellData.win_rate
                        });
                    }
                }
            }
            
            return { heatmap };
        } catch (error) {
            console.error('Error fetching time analysis data:', error);
            throw error;
        }
    }
    
    async fetchAnalysisData() {
        try {
            const queryParams = new URLSearchParams({
                date_range: this.filters.dateRange,
                strategy: this.filters.strategy,
                symbol: this.filters.symbol
            });
    
            const response = await fetch(`/api/trading/analysis/full/?${queryParams}`);
            if (!response.ok) throw new Error('Failed to fetch analysis data');
            
            const data = await response.json();
            
            return {
                metrics: {
                    total_profit: data.metrics.total_profit,
                    win_rate: data.metrics.win_rate,
                    profit_factor: data.metrics.profit_factor,
                    sharpe_ratio: data.metrics.sharpe_ratio
                },
                charts: {
                    equity: {
                        labels: data.equity.dates,
                        datasets: [{
                            label: 'Equity',
                            data: data.equity.values
                        }]
                    },
                    drawdown: {
                        labels: data.drawdown.dates,
                        datasets: [{
                            label: 'Drawdown',
                            data: data.drawdown.values
                        }]
                    },
                    distribution: {
                        labels: data.distribution.ranges,
                        datasets: [{
                            label: 'Trade Distribution',
                            data: data.distribution.frequencies
                        }]
                    },
                    timeAnalysis: {
                        datasets: [{
                            data: this.transformTimeData(data.time_analysis)
                        }]
                    }
                },
                trades: data.trades
            };
        } catch (error) {
            console.error('Error fetching analysis data:', error);
            throw error;
        }
    }
    
    transformTimeData(timeData) {
        // Transform time analysis data for heatmap
        const heatmap = [];
        for (let day = 0; day < 5; day++) {
            for (let hour = 0; hour < 24; hour++) {
                const cellData = timeData.find(d => d.day === day && d.hour === hour);
                if (cellData) {
                    heatmap.push({
                        x: hour,
                        y: day,
                        v: cellData.win_rate
                    });
                }
            }
        }
        return heatmap;
    }
}

// Initialize Performance Analyzer
const performanceAnalyzer = new PerformanceAnalyzer();