// static/js/dashboard/widgets.js
class DashboardWidgets {
    constructor() {
        this.performanceChart = null;
        this.updateInterval = null;
        this.initializeWidgets();
    }

    initializeWidgets() {
        this.initializePerformanceChart();
        this.initializeMarketWatch();
        this.startUpdateInterval();
    }

    initializePerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: window.performanceData.dates,
                datasets: [{
                    label: 'Balance',
                    data: window.performanceData.balance,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
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
                        beginAtZero: false
                    }
                }
            }
        });
    }

    initializeMarketWatch() {
        document.querySelectorAll('.symbol-row').forEach(row => {
            row.addEventListener('click', () => {
                const symbol = row.dataset.symbol;
                this.updateChart(symbol);
            });
        });
    }

    startUpdateInterval() {
        this.updateInterval = setInterval(() => {
            this.updatePrices();
            this.updateOpenPositions();
            this.updateAccountInfo();
        }, 1000);
    }

    async updatePrices() {
        try {
            const response = await fetch('/api/market-data/prices/');
            const data = await response.json();
            
            data.forEach(symbol => {
                const row = document.querySelector(`tr[data-symbol="${symbol.name}"]`);
                if (row) {
                    row.querySelector('.bid').textContent = symbol.bid.toFixed(5);
                    row.querySelector('.ask').textContent = symbol.ask.toFixed(5);
                    
                    const changeEl = row.querySelector('.change');
                    changeEl.textContent = `${symbol.change.toFixed(2)}%`;
                    changeEl.className = `change ${symbol.change >= 0 ? 'text-success' : 'text-danger'}`;
                }
            });
        } catch (error) {
            console.error('Error updating prices:', error);
        }
    }

    async updateOpenPositions() {
        try {
            const response = await fetch('/api/trading/positions/');
            const data = await response.json();
            
            const tbody = document.getElementById('openPositionsBody');
            tbody.innerHTML = data.positions.map(position => this.createPositionRow(position)).join('');
        } catch (error) {
            console.error('Error updating positions:', error);
        }
    }

    async updateAccountInfo() {
        try {
            const response = await fetch('/api/trading/account/');
            const data = await response.json();
            
            document.getElementById('accountBalance').textContent = `$${data.balance.toFixed(2)}`;
            document.getElementById('accountEquity').textContent = `$${data.equity.toFixed(2)}`;
            document.getElementById('openPL').textContent = `$${data.profit.toFixed(2)}`;
            document.getElementById('dailyPL').textContent = `$${data.daily_profit.toFixed(2)}`;
        } catch (error) {
            console.error('Error updating account info:', error);
        }
    }

    createPositionRow(position) {
        return `
            <tr data-ticket="${position.ticket}">
                <td>${position.ticket}</td>
                <td>${position.symbol}</td>
                <td>
                    <span class="badge ${position.type === 'BUY' ? 'bg-success' : 'bg-danger'}">
                        ${position.type}
                    </span>
                </td>
                <td>${position.volume}</td>
                <td>${position.open_price}</td>
                <td class="current-price">${position.current_price}</td>
                <td>${position.sl || '-'}</td>
                <td>${position.tp || '-'}</td>
                <td class="profit ${position.profit >= 0 ? 'text-success' : 'text-danger'}">
                    $${position.profit.toFixed(2)}
                </td>
                <td>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-danger" onclick="closePosition('${position.ticket}')">
                            Close
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="showModifyModal('${position.ticket}')">
                            Modify
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }

    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize widgets
const dashboardWidgets = new DashboardWidgets();