// static/js/trading/dashboard.js
class TradingDashboard {
    constructor() {
        this.updateInterval = null;
        this.initializeEventListeners();
        this.startUpdates();
    }

    initializeEventListeners() {
        // New Order Form
        document.getElementById('newOrderForm')?.addEventListener('submit', this.handleNewOrder.bind(this));

        // Update position size based on risk
        document.getElementById('riskPercent')?.addEventListener('input', this.updatePositionSize.bind(this));

        // Symbol selection change
        document.getElementById('orderSymbol')?.addEventListener('change', this.handleSymbolChange.bind(this));
    }

    startUpdates() {
        // Update every second
        this.updateInterval = setInterval(() => {
            this.updatePrices();
            this.updateAccountInfo();
        }, 1000);
    }

    async handleNewOrder(event) {
        event.preventDefault();

        const formData = {
            symbol: document.getElementById('orderSymbol').value,
            type: document.getElementById('orderType').value,
            volume: document.getElementById('orderVolume').value,
            sl: document.getElementById('orderSL').value || null,
            tp: document.getElementById('orderTP').value || null,
            selected_models: Array.from(
                document.querySelectorAll('input[name="selectedModels"]:checked')
            ).map(cb => cb.value)
        };

        try {
            const response = await fetch('/api/trading/orders/place_order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('Order placed successfully', 'success');
                this.refreshOpenPositions();
                this.closeModal('newOrderModal');
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            this.showNotification('Error placing order', 'error');
            console.error('Error:', error);
        }
    }

    async updatePrices() {
        const currentPrices = document.querySelectorAll('.current-price');
        for (let priceElement of currentPrices) {
            const symbol = priceElement.dataset.symbol;
            try {
                const response = await fetch(`/api/market-data/price/${symbol}/`);
                const data = await response.json();
                priceElement.textContent = data.price.toFixed(5);
            } catch (error) {
                console.error(`Error updating price for ${symbol}:`, error);
            }
        }
    }

    async updateAccountInfo() {
        try {
            const response = await fetch('/api/trading/account-info/');
            const data = await response.json();

            document.getElementById('accountBalance').textContent =
                `$${data.balance.toFixed(2)}`;
            document.getElementById('accountEquity').textContent =
                `$${data.equity.toFixed(2)}`;
            document.getElementById('openPL').textContent =
                `$${data.profit.toFixed(2)}`;
            document.getElementById('marginLevel').textContent =
                `${data.margin_level.toFixed(2)}%`;
        } catch (error) {
            console.error('Error updating account info:', error);
        }
    }

    async updatePositionSize() {
        const riskPercent = document.getElementById('riskPercent').value;
        const symbol = document.getElementById('orderSymbol').value;
        const sl = document.getElementById('orderSL').value;

        if (!symbol || !sl) return;

        try {
            const response = await fetch('/api/trading/calculate-position-size/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    symbol,
                    risk_percent: riskPercent,
                    stop_loss: sl
                })
            });

            const result = await response.json();
            if (result.success) {
                document.getElementById('orderVolume').value = result.position_size;
            }
        } catch (error) {
            console.error('Error calculating position size:', error);
        }
    }

    async refreshOpenPositions() {
        try {
            const response = await fetch('/api/trading/open-positions/');
            const data = await response.json();
            this.updatePositionsTable(data.positions);
        } catch (error) {
            console.error('Error refreshing positions:', error);
        }
    }

    updatePositionsTable(positions) {
        const tbody = document.getElementById('openPositionsTable');
        if (!tbody) return;

        tbody.innerHTML = positions.length ?
            positions.map(position => this.createPositionRow(position)).join('') :
            '<tr><td colspan="10" class="text-center">No open positions</td></tr>';
    }

    createPositionRow(position) {
        return `
            <tr>
                <td>${position.ticket}</td>
                <td>${position.symbol}</td>
                <td>
                    <span class="badge ${position.type === 'BUY' ? 'bg-success' : 'bg-danger'}">
                        ${position.type}
                    </span>
                </td>
                <td>${position.volume}</td>
                <td>${position.open_price}</td>
                <td class="current-price" data-symbol="${position.symbol}">
                    ${position.current_price}
                </td>
                <td>${position.sl || '-'}</td>
                <td>${position.tp || '-'}</td>
                <td class="${position.profit >= 0 ? 'text-success' : 'text-danger'}">
                    $${position.profit.toFixed(2)}
                </td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="tradingDashboard.closePosition(${position.ticket})">
                        Close
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="tradingDashboard.showModifyModal(${position.ticket})">
                        Modify
                    </button>
                </td>
            </tr>
        `;
    }

    showNotification(message, type) {
        // Tạo hoặc lấy container cho notifications
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px; 
                right: 20px;
                z-index: 9999;
                width: 350px;
            `;
            document.body.appendChild(container);
        }

        // Tạo notification mới
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            animation: slideIn 0.5s ease forwards;
            display: flex;
            justify-content: space-between;
            align-items: center;
        `;

        // Set background color based on type
        if (type === 'success') {
            notification.style.backgroundColor = '#4caf50';
            notification.style.color = 'white';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#f44336';
            notification.style.color = 'white';
        } else if (type === 'warning') {
            notification.style.backgroundColor = '#ff9800';
            notification.style.color = 'white';
        } else {
            notification.style.backgroundColor = '#2196f3';
            notification.style.color = 'white';
        }

        // Add content
        notification.innerHTML = `
            <div class="message">${message}</div>
            <button class="close-btn" style="
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 20px;
                margin-left: 10px;
            ">&times;</button>
        `;

        // Add to container
        container.appendChild(notification);

        // Add close functionality
        const closeBtn = notification.querySelector('.close-btn');
        closeBtn.addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.5s ease forwards';
            setTimeout(() => {
                notification.remove();
                if (container.children.length === 0) {
                    container.remove();
                }
            }, 500);
        });

        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.style.animation = 'slideOut 0.5s ease forwards';
                setTimeout(() => {
                    notification.remove();
                    if (container.children.length === 0) {
                        container.remove();
                    }
                }, 500);
            }
        }, 5000);

        // Add keyframe animations
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                
                @keyframes slideOut {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(100%);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(styles);
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    closeModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) modal.hide();
    }
}

// Initialize dashboard
const tradingDashboard = new TradingDashboard();