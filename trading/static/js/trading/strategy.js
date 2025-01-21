// static/js/trading/strategy.js
class StrategyManager {
    constructor() {
        this.charts = {};
        this.initializeEventListeners();
        this.loadCharts();
    }

    initializeEventListeners() {
        // New Strategy Form
        document.getElementById('newStrategyForm')?.addEventListener('submit',
            this.handleNewStrategy.bind(this));

        // Strategy Filters
        document.getElementById('strategyFilter')?.addEventListener('change',
            this.updateCharts.bind(this));

        // Model Weight Sliders
        document.querySelectorAll('.model-weight-slider').forEach(slider => {
            slider.addEventListener('input', this.updateModelWeights.bind(this));
        });
    }

    async loadCharts() {
        await this.initializePerformanceChart();
        await this.initializeModelContributionsChart();
    }

    async initializePerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx) return;

        try {
            const response = await fetch('/api/trading/strategies/performance/');
            const data = await response.json();

            this.charts.performance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: 'Equity',
                        data: data.equity,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Strategy Performance'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error loading performance chart:', error);
        }
    }

    async initializeModelContributionsChart() {
        const ctx = document.getElementById('modelContributionsChart');
        if (!ctx) return;

        try {
            const response = await fetch('/api/trading/strategies/model-contributions/');
            const data = await response.json();

            this.charts.contributions = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.models,
                    datasets: [{
                        data: data.contributions,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 206, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)',
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        title: {
                            display: true,
                            text: 'Model Contributions'
                        }
                    }
                }
            });
        } catch (error) {
            console.error('Error loading contributions chart:', error);
        }
    }

    async handleNewStrategy(event) {
        event.preventDefault();

        const formData = new FormData(event.target);
        const strategyData = {
            name: formData.get('name'),
            symbol: formData.get('symbol'),
            timeframe: formData.get('timeframe'),
            parameters: {
                entry_conditions: this.getEntryConditions(),
                exit_conditions: this.getExitConditions()
            },
            risk_settings: {
                risk_per_trade: formData.get('riskPerTrade'),
                max_trades: formData.get('maxTrades')
            },
            selected_models: Array.from(
                document.querySelectorAll('input[name="selectedModels"]:checked')
            ).map(cb => cb.value),
            model_weights: this.getModelWeights()
        };

        try {
            const response = await fetch('/api/trading/strategies/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(strategyData)
            });

            const result = await response.json();
            if (result.success) {
                this.showNotification('Strategy created successfully', 'success');
                location.reload();
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            console.error('Error creating strategy:', error);
            this.showNotification('Error creating strategy', 'error');
        }
    }

    getEntryConditions() {
        const conditions = {};
        document.querySelectorAll('.entry-condition').forEach(condition => {
            conditions[condition.dataset.type] = {
                enabled: condition.querySelector('.condition-enabled').checked,
                parameters: this.getConditionParameters(condition)
            };
        });
        return conditions;
    }

    getExitConditions() {
        const conditions = {};
        document.querySelectorAll('.exit-condition').forEach(condition => {
            conditions[condition.dataset.type] = {
                enabled: condition.querySelector('.condition-enabled').checked,
                parameters: this.getConditionParameters(condition)
            };
        });
        return conditions;
    }

    getConditionParameters(conditionElement) {
        const params = {};
        conditionElement.querySelectorAll('.condition-parameter').forEach(param => {
            params[param.name] = param.value;
        });
        return params;
    }

    getModelWeights() {
        const weights = {};
        document.querySelectorAll('.model-weight-slider').forEach(slider => {
            weights[slider.dataset.modelId] = parseFloat(slider.value);
        });
        return weights;
    }

    async showStrategyDetails(strategyId) {
        try {
            const response = await fetch(`/api/trading/strategies/${strategyId}/details/`);
            const data = await response.json();
            this.updateStrategyDetailsModal(data);

            const modal = new bootstrap.Modal(document.getElementById('strategyDetailsModal'));
            modal.show();
        } catch (error) {
            console.error('Error loading strategy details:', error);
            this.showNotification('Error loading strategy details', 'error');
        }
    }

    updateStrategyDetailsModal(data) {
        // Update basic info
        document.getElementById('strategyName').textContent = data.name;
        document.getElementById('strategySymbol').textContent = data.symbol;
        document.getElementById('strategyTimeframe').textContent = data.timeframe;
        document.getElementById('strategyRisk').textContent =
            `${data.risk_settings.risk_per_trade}%`;

        // Update performance metrics
        document.getElementById('strategyTotalTrades').textContent = data.total_trades;
        document.getElementById('strategyWinRate').textContent =
            `${data.win_rate.toFixed(2)}%`;
        document.getElementById('strategyProfitFactor').textContent =
            data.profit_factor.toFixed(2);
        document.getElementById('strategySharpeRatio').textContent =
            data.sharpe_ratio.toFixed(2);

        // Update charts
        this.updateStrategyCharts(data);

        // Update model weights
        this.updateModelWeightsDisplay(data.model_weights);

        // Update trades table
        this.updateStrategyTradesTable(data.recent_trades);
    }

    updateStrategyCharts(data) {
        // Update equity chart
        if (this.charts.strategyEquity) {
            this.charts.strategyEquity.destroy();
        }

        const equityCtx = document.getElementById('strategyEquityChart');
        this.charts.strategyEquity = new Chart(equityCtx, {
            type: 'line',
            data: {
                labels: data.equity_curve.dates,
                datasets: [{
                    label: 'Equity',
                    data: data.equity_curve.values,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });

        // Update drawdown chart
        if (this.charts.strategyDrawdown) {
            this.charts.strategyDrawdown.destroy();
        }

        const drawdownCtx = document.getElementById('strategyDrawdownChart');
        this.charts.strategyDrawdown = new Chart(drawdownCtx, {
            type: 'line',
            data: {
                labels: data.drawdown.dates,
                datasets: [{
                    label: 'Drawdown',
                    data: data.drawdown.values,
                    borderColor: 'rgb(255, 99, 132)',
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        reverse: true
                    }
                }
            }
        });
    }

    updateModelWeightsDisplay(weights) {
        const container = document.getElementById('modelWeightsContainer');
        container.innerHTML = Object.entries(weights)
            .map(([modelId, weight]) => `
                <div class="model-weight">
                    <label>${this.getModelName(modelId)}</label>
                    <div class="progress">
                        <div class="progress-bar" role="progressbar" 
                             style="width: ${weight * 100}%">
                            ${(weight * 100).toFixed(1)}%
                        </div>
                    </div>
                </div>
            `).join('');
    }

    updateStrategyTradesTable(trades) {
        const tbody = document.getElementById('strategyTradesTable');
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td>${new Date(trade.open_time).toLocaleString()}</td>
                <td>
                    <span class="badge ${trade.type === 'BUY' ? 'bg-success' : 'bg-danger'}">
                        ${trade.type}
                    </span>
                </td>
                <td>${trade.open_price}</td>
                <td>${trade.close_price || '-'}</td>
                <td class="${trade.profit >= 0 ? 'text-success' : 'text-danger'}">
                    $${trade.profit.toFixed(2)}
                </td>
                <td>${trade.models_used.join(', ')}</td>
            </tr>
        `).join('');
    }

    getModelName(modelId) {
        // Implementation to get model name from ID
        const modelElement = document.querySelector(`[data-model-id="${modelId}"]`);
        return modelElement ? modelElement.dataset.modelName : `Model ${modelId}`;
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    showNotification(message, type) {
        // Kiểm tra xem container đã tồn tại chưa
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
            `;
            document.body.appendChild(container);
        }

        // Tạo notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        notification.role = 'alert';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Thêm notification vào container
        container.appendChild(notification);

        // Auto hide sau 5 giây
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();

                // Xóa container nếu không còn notification nào
                if (container.children.length === 0) {
                    container.remove();
                }
            }, 150);
        }, 5000);

        // Handle close button
        const closeButton = notification.querySelector('.btn-close');
        closeButton.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
                if (container.children.length === 0) {
                    container.remove();
                }
            }, 150);
        });
    }
}

// Initialize Strategy Manager
const strategyManager = new StrategyManager();