"""
Configurable parameters for the trading bot.

These variables define the behaviour of the strategy and risk
management.  You can adjust them without modifying the core logic.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class BotConfig:
    """Holds configurable parameters for the trading bot."""
    
    # --- General Settings ---
    
    # Symbol to trade (e.g. "EURUSD")
    symbol: str = "EURUSD"
    
    # Broker type (e.g., 'mt5', 'oanda')
    broker_type: str = "mt5"
    
    # Enable debug messages to print out internal state
    enable_debug: bool = True
    
    # Magic number used to tag orders from this EA/bot
    magic_number: int = 987654
    
    # --- Strategy Settings ---
    
    # Distance in pips the price must travel within the time window to trigger a trade
    distance_pips: float = 10.0
    
    # Time window (seconds) in which the price movement must occur before resetting
    time_seconds: int = 60
    
    # --- Risk Management Settings ---
    
    # Risk management strategy to use
    risk_strategy: str = "fixed_fractional"  # Options: 'fixed_fractional', 'fixed_lot'
    
    # Fixed lot size (used when risk_strategy is 'fixed_lot' or mm is 0)
    lot_size: float = 0.01
    
    # Money management coefficient (legacy, use risk_percent instead)
    # When >0, lot size is calculated as (equity / 10,000) * mm
    mm: float = 0.0
    
    # Maximum lot size allowed
    max_lot_size: float = 100.0
    
    # Minimum lot size allowed
    min_lot_size: float = 0.01
    
    # Risk per trade as a percentage of account equity (0.0 - 100.0)
    risk_percent: float = 1.0
    
    # Maximum number of open positions allowed (0 = unlimited)
    max_open_positions: int = 0
    
    # Maximum exposure as a percentage of account equity (0.0 - 100.0)
    max_exposure_percent: float = 50.0
    
    # --- Order Settings ---
    
    # Take profit in pips
    take_profit_pips: float = 20.0
    
    # Stop loss in pips
    stop_loss_pips: float = 15.0
    
    # Trailing stop in pips (0 disables trailing stop)
    trailing_stop: float = 0.0
    
    # Slippage tolerance in pips
    slippage_pips: float = 1.0
    
    # --- Additional Settings ---
    
    # Custom parameters that can be used by strategies
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, **kwargs) -> None:
        """Update configuration parameters.
        
        Args:
            **kwargs: Key-value pairs of parameters to update.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary.
        
        Returns:
            A dictionary containing all configuration parameters.
        """
        return {
            name: value for name, value in self.__dict__.items()
            if not name.startswith('_')
        }
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BotConfig':
        """Create a BotConfig instance from a dictionary.
        
        Args:
            config_dict: Dictionary containing configuration parameters.
            
        Returns:
            A new BotConfig instance.
        """
        return cls(**config_dict)
