from typing import List, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from datetime import datetime
import logging

@dataclass
class Position:
    """Represents a trading position"""
    side: str  # 'long' or 'short'
    entry_price: float
    size: float
    leverage: float
    entry_time: datetime
    liquidation_price: float
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL"""
        if self.side == 'long':
            return (current_price - self.entry_price) * self.size * self.leverage
        else:  # short
            return (self.entry_price - current_price) * self.size * self.leverage
    
    def is_liquidated(self, current_price: float) -> bool:
        """Check if position should be liquidated"""
        if self.side == 'long':
            return current_price <= self.liquidation_price
        else:  # short
            return current_price >= self.liquidation_price

@dataclass
class Trade:
    """Represents a completed trade"""
    side: str
    entry_price: float
    exit_price: float
    size: float
    leverage: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    reason: str  # 'trend_reversal', 'liquidation', 'manual'

class TrendFollowingStrategy:
    """Trend following strategy implementation"""
    
    def __init__(self, 
                 lookback_periods: int = 3,
                 min_trend_strength: float = 0.0005,  # 0.05% minimum price change
                 leverage: float = 5.0,
                 position_size: float = 100.0,  # USDC
                 trading_fee: float = 0.001,  # 0.1%
                 liquidation_threshold: float = 0.8):  # 80% of position
        
        self.lookback_periods = lookback_periods
        self.min_trend_strength = min_trend_strength
        self.leverage = leverage
        self.position_size = position_size
        self.trading_fee = trading_fee
        self.liquidation_threshold = liquidation_threshold
        
        self.price_history: List[Tuple[datetime, float]] = []
        self.current_position: Optional[Position] = None
        self.completed_trades: List[Trade] = []
        self.balance = 1000.0  # Starting balance in USDC
        self.total_fees_paid = 0.0
        
    def add_price(self, timestamp: datetime, price: float):
        """Add new price data point"""
        self.price_history.append((timestamp, price))
        
        # Keep only recent data to manage memory
        if len(self.price_history) > 1000:
            self.price_history = self.price_history[-500:]
    
    def detect_trend(self) -> Optional[str]:
        """
        Detect trend direction based on recent price action
        
        Returns:
            'bullish', 'bearish', or None
        """
        if len(self.price_history) < self.lookback_periods + 1:
            return None
        
        recent_prices = [price for _, price in self.price_history[-(self.lookback_periods + 1):]]
        
        # Check for higher highs (bullish trend)
        higher_highs = all(
            recent_prices[i] > recent_prices[i-1] * (1 + self.min_trend_strength)
            for i in range(1, len(recent_prices))
        )
        
        # Check for lower lows (bearish trend)
        lower_lows = all(
            recent_prices[i] < recent_prices[i-1] * (1 - self.min_trend_strength)
            for i in range(1, len(recent_prices))
        )
        
        if higher_highs:
            return 'bullish'
        elif lower_lows:
            return 'bearish'
        else:
            return None
    
    def calculate_liquidation_price(self, entry_price: float, side: str) -> float:
        """Calculate liquidation price based on leverage"""
        liquidation_distance = entry_price / self.leverage * self.liquidation_threshold
        
        if side == 'long':
            return entry_price - liquidation_distance
        else:  # short
            return entry_price + liquidation_distance
    
    def calculate_trading_fee(self, notional_value: float) -> float:
        """Calculate trading fee"""
        return notional_value * self.trading_fee
    
    def open_position(self, side: str, price: float, timestamp: datetime) -> bool:
        """
        Open a new position
        
        Returns:
            True if position opened successfully
        """
        if self.current_position is not None:
            return False
        
        # Calculate position details
        notional_value = self.position_size * self.leverage
        fee = self.calculate_trading_fee(notional_value)
        
        # Check if we have enough balance for fees
        if self.balance < fee:
            logging.warning(f"Insufficient balance for fees. Required: {fee}, Available: {self.balance}")
            return False
        
        # Deduct fee from balance
        self.balance -= fee
        self.total_fees_paid += fee
        
        # Calculate liquidation price
        liquidation_price = self.calculate_liquidation_price(price, side)
        
        # Create position
        self.current_position = Position(
            side=side,
            entry_price=price,
            size=self.position_size,
            leverage=self.leverage,
            entry_time=timestamp,
            liquidation_price=liquidation_price
        )
        
        logging.info(f"Opened {side} position at ${price:.4f}, liquidation at ${liquidation_price:.4f}")
        return True
    
    def close_position(self, price: float, timestamp: datetime, reason: str = 'trend_reversal') -> Optional[Trade]:
        """
        Close current position
        
        Returns:
            Trade object if position closed
        """
        if self.current_position is None:
            return None
        
        # Calculate PnL
        pnl = self.current_position.calculate_pnl(price)
        
        # Calculate and deduct closing fee
        notional_value = self.current_position.size * self.leverage
        fee = self.calculate_trading_fee(notional_value)
        self.balance -= fee
        self.total_fees_paid += fee
        
        # Net PnL after fees
        net_pnl = pnl - fee
        self.balance += net_pnl
        
        # Create trade record
        trade = Trade(
            side=self.current_position.side,
            entry_price=self.current_position.entry_price,
            exit_price=price,
            size=self.current_position.size,
            leverage=self.current_position.leverage,
            entry_time=self.current_position.entry_time,
            exit_time=timestamp,
            pnl=net_pnl,
            reason=reason
        )
        
        self.completed_trades.append(trade)
        logging.info(f"Closed {self.current_position.side} position at ${price:.4f}, PnL: ${net_pnl:.2f}")
        
        self.current_position = None
        return trade
    
    def check_liquidation(self, price: float, timestamp: datetime) -> Optional[Trade]:
        """Check if current position should be liquidated"""
        if self.current_position is None:
            return None
        
        if self.current_position.is_liquidated(price):
            return self.close_position(price, timestamp, 'liquidation')
        
        return None
    
    def process_price_update(self, timestamp: datetime, price: float) -> Optional[str]:
        """
        Process new price update and make trading decisions
        
        Returns:
            Action taken ('opened_long', 'opened_short', 'closed_position', 'liquidated', None)
        """
        self.add_price(timestamp, price)
        
        # Check for liquidation first
        if self.check_liquidation(price, timestamp):
            return 'liquidated'
        
        # Detect current trend
        trend = self.detect_trend()
        
        if self.current_position is None:
            # No position, look for entry signals
            if trend == 'bullish':
                if self.open_position('long', price, timestamp):
                    return 'opened_long'
            elif trend == 'bearish':
                if self.open_position('short', price, timestamp):
                    return 'opened_short'
        else:
            # Have position, look for exit signals
            current_side = self.current_position.side
            
            # Exit if trend reverses
            if (current_side == 'long' and trend == 'bearish') or \
               (current_side == 'short' and trend == 'bullish'):
                self.close_position(price, timestamp, 'trend_reversal')
                return 'closed_position'
        
        return None
    
    def get_current_pnl(self, current_price: float) -> float:
        """Get current unrealized PnL"""
        if self.current_position is None:
            return 0.0
        return self.current_position.calculate_pnl(current_price)
    
    def get_total_realized_pnl(self) -> float:
        """Get total realized PnL from completed trades"""
        return sum(trade.pnl for trade in self.completed_trades)
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage"""
        if not self.completed_trades:
            return 0.0
        
        winning_trades = sum(1 for trade in self.completed_trades if trade.pnl > 0)
        return (winning_trades / len(self.completed_trades)) * 100
    
    def get_stats(self) -> dict:
        """Get comprehensive trading statistics"""
        total_trades = len(self.completed_trades)
        realized_pnl = self.get_total_realized_pnl()
        win_rate = self.get_win_rate()
        
        if total_trades > 0:
            avg_trade = realized_pnl / total_trades
            winning_trades = [t for t in self.completed_trades if t.pnl > 0]
            losing_trades = [t for t in self.completed_trades if t.pnl < 0]
            
            avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0
            
            profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        else:
            avg_trade = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
        
        return {
            'total_trades': total_trades,
            'realized_pnl': realized_pnl,
            'win_rate': win_rate,
            'avg_trade': avg_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_fees': self.total_fees_paid,
            'current_balance': self.balance
        }
