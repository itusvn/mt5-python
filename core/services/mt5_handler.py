# core/services/mt5_handler.py
import MetaTrader5 as mt5
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import time
from pathlib import Path
from django.conf import settings
from utils.exceptions import MT5ConnectionError

logger = logging.getLogger(__name__)


class MT5Handler:
    """Singleton class để quản lý kết nối MT5"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MT5Handler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialized = True
            self.connected = False
            self.last_error = None
            self.config = self.load_config()
            self.setup_logging()

    def setup_logging(self):
        """Setup logging"""
        log_dir = Path(settings.BASE_DIR) / "logs"
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(log_dir / "mt5_connection.log")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    def load_config(self) -> Dict:
        """Load MT5 configuration"""
        return {
            "path": settings.MT5_PATH,
            "login": settings.MT5_LOGIN,
            "password": settings.MT5_PASSWORD,
            "server": settings.MT5_SERVER,
            "timeout": settings.MT5_TIMEOUT,
            "retry_count": 3,
            "retry_delay": 1,
        }

    def connect(self) -> bool:
        """Thiết lập kết nối với MT5"""
        if self.connected:
            return True

        try:
            # Initialize MT5
            logger.info("Initializing MT5...")
            initialized = mt5.initialize(
                path=str(self.config["path"]),
                login=self.config["login"],
                password=self.config["password"],
                server=self.config["server"],
                timeout=self.config["timeout"],
            )

            if not initialized:
                raise MT5ConnectionError(
                    f"MT5 initialization failed: {mt5.last_error()}"
                )

            # Verify connection
            if not self._verify_connection():
                raise MT5ConnectionError("Failed to verify MT5 connection")

            self.connected = True
            logger.info("Successfully connected to MT5")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to connect to MT5: {e}")
            return False

    def _verify_connection(self) -> bool:
        """Verify MT5 connection"""
        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                return False
            return terminal_info.connected

        except Exception as e:
            logger.error(f"Connection verification failed: {e}")
            return False

    def disconnect(self):
        """Ngắt kết nối MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")

    def ensure_connected(self) -> bool:
        """Đảm bảo kết nối MT5 được duy trì"""
        if not self.connected:
            retry_count = 0
            while retry_count < self.config["retry_count"]:
                logger.info(f"Attempting to reconnect (attempt {retry_count + 1})...")
                if self.connect():
                    return True
                retry_count += 1
                time.sleep(self.config["retry_delay"])
            return False
        return True

    def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Lấy thông tin tài khoản"""
        if not self.ensure_connected():
            return None

        try:
            account_info = mt5.account_info()
            if account_info is None:
                raise MT5ConnectionError("Failed to get account info")

            return {
                "login": account_info.login,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "profit": account_info.profit,
                "margin": account_info.margin,
                "margin_free": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "leverage": account_info.leverage,
                "currency": account_info.currency,
            }

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_positions(self) -> list:
        """Lấy danh sách positions"""
        if not self.ensure_connected():
            return []

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            return [
                {
                    "ticket": position.ticket,
                    "symbol": position.symbol,
                    "type": position.type,
                    "volume": position.volume,
                    "price_open": position.price_open,
                    "price_current": position.price_current,
                    "sl": position.sl,
                    "tp": position.tp,
                    "profit": position.profit,
                    "magic": position.magic,
                    "comment": position.comment,
                }
                for position in positions
            ]

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def place_order(
        self,
        symbol: str,
        order_type: str,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "",
        magic: int = 0,
    ) -> Dict:
        """Place order"""
        if not self.ensure_connected():
            return {"success": False, "error": "Not connected to MT5"}

        try:
            # Validate symbol
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                raise ValueError(f"Invalid symbol: {symbol}")

            # Prepare order request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": (
                    mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL
                ),
                "price": price or mt5.symbol_info_tick(symbol).ask,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send order
            logger.info(f"Sending order request: {request}")
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Order failed: {result.comment}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            return {
                "success": True,
                "ticket": result.order,
                "volume": result.volume,
                "price": result.price,
            }

        except Exception as e:
            error_msg = f"Error placing order: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def modify_position(
        self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None
    ) -> Dict:
        """Modify position SL/TP"""
        if not self.ensure_connected():
            return {"success": False, "error": "Not connected to MT5"}

        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return {"success": False, "error": f"Position {ticket} not found"}

            position = position[0]
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": sl if sl is not None else position.sl,
                "tp": tp if tp is not None else position.tp,
            }

            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                error_msg = f"Modify failed: {result.comment}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            return {"success": True}

        except Exception as e:
            error_msg = f"Error modifying position: {e}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
