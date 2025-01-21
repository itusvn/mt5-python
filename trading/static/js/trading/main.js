// static/js/trading/main.js

class TradingApp {
    constructor() {
        this.priceSocket = null;
        this.tradeSocket = null;
        this.dashboard = new DashboardWidgets();
        this.initializeWebSockets();
    }

    initializeWebSockets() {
        // Connect to price feed
        this.priceSocket = new WebSocket(
            `ws://${window.location.host}/ws/prices/`
        );
        this.priceSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.dashboard.updatePrices(data);
        };

        // Connect to trade updates
        this.tradeSocket = new WebSocket(
            `ws://${window.location.host}/ws/trades/`
        );
        this.tradeSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleTradeUpdate(data);
        };
    }

    handleTradeUpdate(data) {
        switch(data.type) {
            case 'predictions':
                this.dashboard.updatePredictions(data.data);
                break;
            case 'trade_execution':
                this.dashboard.updatePositions();
                this.showNotification(data.data);
                break;
        }
    }

    cleanup() {
        if (this.priceSocket) {
            this.priceSocket.close();
        }
        if (this.tradeSocket) {
            this.tradeSocket.close();
        }
        this.dashboard.cleanup();
    }
}

// Initialize application
const app = new TradingApp();

// Cleanup on page unload
window.addEventListener('unload', () => {
    app.cleanup();
});