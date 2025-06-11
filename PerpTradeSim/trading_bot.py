import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from jupiter_api import JupiterAPI
from strategy import TrendFollowingStrategy, Trade

class TradingBot:
    """Main trading bot class that coordinates strategy and data fetching"""
    
    def __init__(self, 
                 update_interval: int = 30,  # seconds
                 lookback_periods: int = 3,
                 leverage: float = 5.0,
                 position_size: float = 100.0,
                 trading_fee: float = 0.001):
        
        self.update_interval = update_interval
        self.jupiter_api = JupiterAPI()
        self.strategy = TrendFollowingStrategy(
            lookback_periods=lookback_periods,
            leverage=leverage,
            position_size=position_size,
            trading_fee=trading_fee
        )
        
        self.is_running = False
        self.last_price = None
        self.last_update = None
        self.price_history: List[Dict[str, Any]] = []
        self.trade_log: List[Dict[str, Any]] = []
        self.error_count = 0
        self.max_errors = 10
        
        # Thread for background price updates
        self.update_thread = None
        
    def start(self):
        """Start the trading bot"""
        if self.is_running:
            return
            
        self.is_running = True
        self.error_count = 0
        
        # Start background thread for price updates
        self.update_thread = threading.Thread(target=self._price_update_loop, daemon=True)
        self.update_thread.start()
        
        logging.info("Trading bot started")
    
    def stop(self):
        """Stop the trading bot"""
        self.is_running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
        logging.info("Trading bot stopped")
    
    def _price_update_loop(self):
        """Background loop for fetching price updates"""
        while self.is_running:
            try:
                self._fetch_and_process_price()
                time.sleep(self.update_interval)
                
            except Exception as e:
                logging.error(f"Error in price update loop: {e}")
                self.error_count += 1
                
                if self.error_count >= self.max_errors:
                    logging.error("Max errors reached, stopping bot")
                    self.is_running = False
                    break
                
                time.sleep(min(self.update_interval, 60))  # Wait before retry
    
    def _fetch_and_process_price(self):
        """Fetch current price and process through strategy"""
        price = self.jupiter_api.get_price_with_retry()
        
        if price is None:
            logging.warning("Failed to fetch price from Jupiter API")
            return
        
        timestamp = datetime.now()
        
        # Store price data
        price_data = {
            'timestamp': timestamp,
            'price': price,
            'datetime_str': timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        self.price_history.append(price_data)
        
        # Keep only recent price history
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-500:]
        
        # Process through strategy
        action = self.strategy.process_price_update(timestamp, price)
        
        if action:
            self._log_trading_action(action, price, timestamp)
        
        self.last_price = price
        self.last_update = timestamp
        self.error_count = 0  # Reset error count on success
    
    def _log_trading_action(self, action: str, price: float, timestamp: datetime):
        """Log trading actions"""
        log_entry = {
            'timestamp': timestamp,
            'action': action,
            'price': price,
            'datetime_str': timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if self.strategy.current_position:
            log_entry['position_side'] = self.strategy.current_position.side
            log_entry['position_size'] = self.strategy.current_position.size
            log_entry['leverage'] = self.strategy.current_position.leverage
            log_entry['unrealized_pnl'] = self.strategy.get_current_pnl(price)
        
        self.trade_log.append(log_entry)
        
        # Keep only recent trade log
        if len(self.trade_log) > 100:
            self.trade_log = self.trade_log[-50:]
        
        logging.info(f"Trading action: {action} at ${price:.4f}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        status = {
            'is_running': self.is_running,
            'last_price': self.last_price,
            'last_update': self.last_update,
            'error_count': self.error_count,
            'price_history_count': len(self.price_history),
            'trade_log_count': len(self.trade_log)
        }
        
        # Add position info
        if self.strategy.current_position:
            pos = self.strategy.current_position
            status['current_position'] = {
                'side': pos.side,
                'entry_price': pos.entry_price,
                'size': pos.size,
                'leverage': pos.leverage,
                'entry_time': pos.entry_time,
                'liquidation_price': pos.liquidation_price,
                'unrealized_pnl': self.strategy.get_current_pnl(self.last_price) if self.last_price else 0
            }
        else:
            status['current_position'] = None
        
        return status
    
    def get_price_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get price history"""
        if limit:
            return self.price_history[-limit:]
        return self.price_history.copy()
    
    def get_trade_log(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get trade log"""
        if limit:
            return self.trade_log[-limit:]
        return self.trade_log.copy()
    
    def get_completed_trades(self) -> List[Trade]:
        """Get completed trades from strategy"""
        return self.strategy.completed_trades.copy()
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get strategy statistics"""
        return self.strategy.get_stats()
    
    def manual_close_position(self) -> Optional[Trade]:
        """Manually close current position"""
        if not self.strategy.current_position:
            logging.warning("Manual close failed: No current position")
            return None
            
        if not self.last_price:
            logging.warning("Manual close failed: No price data available")
            return None
        
        logging.info(f"Manual close requested for {self.strategy.current_position.side} position at ${self.last_price:.4f}")
        
        trade = self.strategy.close_position(
            self.last_price, 
            datetime.now(), 
            'manual'
        )
        
        if trade:
            self._log_trading_action('manual_close', self.last_price, datetime.now())
            logging.info(f"Manual close successful: PnL ${trade.pnl:.2f}")
        else:
            logging.error("Manual close failed: Strategy close_position returned None")
        
        return trade
    
    def update_strategy_params(self, 
                             leverage: Optional[float] = None,
                             position_size: Optional[float] = None,
                             lookback_periods: Optional[int] = None,
                             min_trend_strength: Optional[float] = None):
        """Update strategy parameters"""
        if leverage is not None:
            self.strategy.leverage = leverage
        if position_size is not None:
            self.strategy.position_size = position_size
        if lookback_periods is not None:
            self.strategy.lookback_periods = lookback_periods
        if min_trend_strength is not None:
            self.strategy.min_trend_strength = min_trend_strength
        
        logging.info("Strategy parameters updated")
    
    def reset_strategy(self):
        """Reset strategy state (clear positions and history)"""
        # Close any open position first
        if self.strategy.current_position:
            self.manual_close_position()
        
        # Reset strategy state
        self.strategy.completed_trades.clear()
        self.strategy.balance = 1000.0
        self.strategy.total_fees_paid = 0.0
        self.trade_log.clear()
        
        logging.info("Strategy reset")
