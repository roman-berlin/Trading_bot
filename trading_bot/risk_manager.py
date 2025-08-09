"""
Risk management module for the trading bot.

This module provides a comprehensive risk management system with multiple
position sizing strategies and risk management rules. It implements the
IRiskManager interface and provides concrete implementations of different
risk management strategies.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, Type, Union

from .interfaces import IRiskManager
from .container import Container
from .config import BotConfig

logger = logging.getLogger(__name__)


@dataclass
class PositionSizeResult:
    """Result of a position size calculation."""
    size: float  # Position size in lots
    risk_amount: float  # Amount of account equity at risk
    risk_percent: float  # Percentage of account equity at risk
    stop_loss_pips: float  # Stop loss in pips


class BaseRiskManager(IRiskManager, ABC):
    """Base class for risk management strategies.
    
    This class provides common functionality for all risk management strategies,
    including position size calculation and validation.
    """
    
    def __init__(self, config: BotConfig, enable_debug: bool = False):
        """Initialize the risk manager.
        
        Args:
            config: The bot configuration.
            enable_debug: Whether to enable debug logging.
        """
        self.config = config
        self.enable_debug = enable_debug
        self._pip_value = None
    
    def set_pip_value(self, pip_value: float) -> None:
        """Set the pip value for the current symbol.
        
        Args:
            pip_value: The value of one pip in the account currency.
        """
        self._pip_value = pip_value
    
    @abstractmethod
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        account_equity: float,
        risk_percent: float = None
    ) -> PositionSizeResult:
        """Calculate the appropriate position size based on risk parameters.
        
        Args:
            symbol: The trading symbol.
            entry_price: The entry price for the position.
            stop_loss_price: The stop loss price for the position.
            account_equity: The current account equity.
            risk_percent: The percentage of account equity to risk (optional).
                
        Returns:
            A PositionSizeResult object containing the calculated position size
            and risk information.
        """
        pass
    
    def validate_order(
        self,
        symbol: str,
        order_type: str,
        size: float,
        price: float,
        stop_loss: float,
        take_profit: float,
        account_equity: float
    ) -> Tuple[bool, str]:
        """Validate an order against risk management rules.
        
        Args:
            symbol: The trading symbol.
            order_type: The order type (e.g., 'buy', 'sell').
            size: The position size in lots.
            price: The entry price.
            stop_loss: The stop loss price.
            take_profit: The take profit price.
            account_equity: The current account equity.
            
        Returns:
            A tuple of (is_valid, reason) where is_valid is a boolean indicating
            whether the order is valid, and reason is a string explaining why
            the order is invalid (if applicable).
        """
        # Basic validation
        if size <= 0:
            return False, "Position size must be greater than zero"
            
        if stop_loss is not None and stop_loss <= 0:
            return False, "Stop loss must be greater than zero"
            
        if take_profit is not None and take_profit <= 0:
            return False, "Take profit must be greater than zero"
            
        # Check if we have enough margin (simplified check)
        # In a real implementation, you would query the broker for margin requirements
        required_margin = size * price * 100000  # Simplified calculation
        if required_margin > account_equity * 0.9:  # Don't use more than 90% of equity
            return False, "Insufficient margin for this position size"
            
        return True, ""
    
    def update_risk_parameters(self, **params) -> None:
        """Update risk management parameters.
        
        Args:
            **params: Key-value pairs of parameters to update.
        """
        for key, value in params.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                if self.enable_debug:
                    logger.debug(f"Updated {key} to {value}")


class FixedFractionalRiskManager(BaseRiskManager):
    """Fixed fractional position sizing based on account equity.
    
    This risk manager calculates position size based on a fixed percentage
    of account equity to risk per trade.
    """
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        account_equity: float,
        risk_percent: float = None
    ) -> PositionSizeResult:
        """Calculate position size using fixed fractional position sizing.
        
        Args:
            symbol: The trading symbol.
            entry_price: The entry price for the position.
            stop_loss_price: The stop loss price for the position.
            account_equity: The current account equity.
            risk_percent: The percentage of account equity to risk.
                If not provided, uses the value from the config.
                
        Returns:
            A PositionSizeResult object.
        """
        if self._pip_value is None:
            raise ValueError("Pip value not set. Call set_pip_value() first.")
            
        # Use config risk percent if not provided
        if risk_percent is None:
            risk_percent = self.config.risk_percent if hasattr(self.config, 'risk_percent') else 1.0
            
        # Calculate risk amount in account currency
        risk_amount = account_equity * (risk_percent / 100.0)
        
        # Calculate stop loss in pips
        price_diff = abs(entry_price - stop_loss_price)
        stop_loss_pips = price_diff / self._pip_value
        
        # Calculate value per pip for the position
        value_per_pip = self._pip_value * (100000 * self.config.lot_size)
        
        # Calculate position size in lots
        if stop_loss_pips > 0 and value_per_pip > 0:
            position_size = (risk_amount / stop_loss_pips) / value_per_pip
        else:
            position_size = 0.0
            
        # Round down to the nearest 0.01 lot
        position_size = (position_size * 100 // 1) / 100
        
        # Apply minimum and maximum position size
        min_lot = getattr(self.config, 'min_lot_size', 0.01)
        max_lot = getattr(self.config, 'max_lot_size', 100.0)
        position_size = max(min(position_size, max_lot), min_lot)
        
        return PositionSizeResult(
            size=position_size,
            risk_amount=risk_amount,
            risk_percent=risk_percent,
            stop_loss_pips=stop_loss_pips
        )


class FixedLotSizeRiskManager(BaseRiskManager):
    """Fixed position sizing using a constant lot size.
    
    This risk manager uses a fixed lot size for all trades, regardless of
    account equity or stop loss distance.
    """
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        account_equity: float,
        risk_percent: float = None
    ) -> PositionSizeResult:
        """Calculate position size using a fixed lot size.
        
        Args:
            symbol: The trading symbol.
            entry_price: The entry price for the position.
            stop_loss_price: The stop loss price for the position.
            account_equity: The current account equity.
            risk_percent: Not used in this implementation.
                
        Returns:
            A PositionSizeResult object.
        """
        if self._pip_value is None:
            raise ValueError("Pip value not set. Call set_pip_value() first.")
            
        # Use fixed lot size from config
        position_size = self.config.lot_size
        
        # Calculate stop loss in pips
        price_diff = abs(entry_price - stop_loss_price)
        stop_loss_pips = price_diff / self._pip_value
        
        # Calculate risk amount in account currency
        value_per_pip = self._pip_value * (100000 * position_size)
        risk_amount = stop_loss_pips * value_per_pip
        risk_percent = (risk_amount / account_equity) * 100 if account_equity > 0 else 0
        
        return PositionSizeResult(
            size=position_size,
            risk_amount=risk_amount,
            risk_percent=risk_percent,
            stop_loss_pips=stop_loss_pips
        )


class RiskManagerFactory:
    """Factory for creating risk management strategies."""
    
    # Available risk management strategies
    STRATEGIES = {
        'fixed_fractional': FixedFractionalRiskManager,
        'fixed_lot': FixedLotSizeRiskManager,
    }
    
    @classmethod
    def create_risk_manager(
        cls,
        strategy_name: str,
        config: BotConfig,
        enable_debug: bool = False,
        container: Optional[Container] = None
    ) -> 'BaseRiskManager':
        """Create a risk manager instance.
        
        Args:
            strategy_name: The name of the risk management strategy.
            config: The bot configuration (legacy, prefer using container).
            enable_debug: Whether to enable debug logging.
            container: The dependency injection container.
            
        Returns:
            A risk manager instance.
            
        Raises:
            ValueError: If the strategy name is not recognized.
        """
        strategy_class = cls.STRATEGIES.get(strategy_name.lower())
        if not strategy_class:
            raise ValueError(f"Unknown risk management strategy: {strategy_name}")
            
        # If a dependency injection container is provided we do not pass
        # it directly into the risk management strategy.  Instead, we
        # construct the strategy with the BotConfig.  The high‑level
        # RiskManager wrapper is responsible for interacting with the
        # container.
        if container is not None:
            if not container.has(BotConfig):
                container.register_instance(BotConfig, config)
            return strategy_class(config=config, enable_debug=enable_debug)
            
        # Legacy behavior - direct instantiation
        return strategy_class(config=config, enable_debug=enable_debug)
    @classmethod
    def get_available_strategies(cls) -> list:
        """Get a list of available risk management strategies.
        
        Returns:
            A list of strategy names.
        """
        return list(cls.STRATEGIES.keys())


class RiskManager(IRiskManager):
    """
    Main risk manager class that implements the IRiskManager interface.
    
    This class provides a high-level interface for risk management operations,
    delegating to specific money management strategies.
    """
    
    def __init__(self, container: Optional[Container] = None, enable_debug: bool = False):
        """Initialize the risk manager.

        Parameters
        ----------
        container : Optional[Container]
            Dependency injection container used to resolve configuration
            and other services.  If omitted or None, a new
            :class:`Container` will be created with a default
            configuration.
        enable_debug : bool, default False
            Whether to enable debug logging for the risk manager.
        """
        # When no container is provided, create a new one with a fresh config
        if container is None:
            # Import here to avoid circular dependency
            from .container import Container as DIContainer
            container = DIContainer()
        self._container = container
        # Resolve config from container
        self.config = container.resolve(BotConfig)
        self.enable_debug = enable_debug
        # Pip value and strategy are set during operation
        self._pip_value = None
        self._strategy = None

        # Initialize the money management strategy
        self._init_strategy()
    
    def _init_strategy(self) -> None:
        """Initialize the money management strategy based on config."""
        # Get the latest config from container
        self.config = self._container.resolve(BotConfig)
        strategy_name = getattr(self.config, 'risk_strategy', 'fixed_fractional')
        
        try:
            # Create the appropriate risk management strategy
            self._strategy = RiskManagerFactory.create_risk_manager(
                strategy_name=strategy_name,
                config=self.config,
                enable_debug=self.enable_debug
            )
            
            # Set pip value if already available
            if self._pip_value is not None:
                self._strategy.set_pip_value(self._pip_value)
            
            logger.info(f"Initialized {strategy_name} risk management strategy")
            
        except Exception as e:
            logger.error(f"Failed to initialize risk management strategy: {e}")
            raise
    
    def set_pip_value(self, pip_value: float) -> None:
        """Set the pip value for the current symbol.
        
        Args:
            pip_value: The value of one pip in the account currency.
        """
        self._pip_value = pip_value
        if self._strategy:
            self._strategy.set_pip_value(pip_value)
    
    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        account_equity: float,
        risk_percent: float = None
    ) -> PositionSizeResult:
        """Calculate the appropriate position size based on risk parameters.
        
        Args:
            symbol: The trading symbol.
            entry_price: The entry price for the position.
            stop_loss_price: The stop loss price for the position.
            account_equity: The current account equity.
            risk_percent: The percentage of account equity to risk (optional).
                
        Returns:
            A PositionSizeResult object containing the calculated position size
            and risk information.
            
        Raises:
            ValueError: If the risk management strategy is not initialized.
        """
        if not self._strategy:
            raise ValueError("Risk management strategy not initialized")
        
        # Use config risk percent if not provided
        if risk_percent is None:
            risk_percent = getattr(self.config, 'risk_percent', 1.0)
        
        # Delegate to the selected strategy
        result = self._strategy.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss_price=stop_loss_price,
            account_equity=account_equity,
            risk_percent=risk_percent
        )
        
        if self.enable_debug:
            logger.debug(
                f"Position size calculated: {result.size:.2f} lots, "
                f"Risk: ${result.risk_amount:.2f} ({result.risk_percent:.2f}%), "
                f"SL: {result.stop_loss_pips:.1f} pips"
            )
        
        return result
    
    def validate_order(
        self,
        symbol: str,
        order_type: str,
        size: float,
        price: float,
        stop_loss: float,
        take_profit: float,
        account_equity: float
    ) -> Tuple[bool, str]:
        """Validate an order against risk management rules.
        
        Args:
            symbol: The trading symbol.
            order_type: The order type (e.g., 'buy', 'sell').
            size: The position size in lots.
            price: The entry price.
            stop_loss: The stop loss price.
            take_profit: The take profit price.
            account_equity: The current account equity.
            
        Returns:
            A tuple of (is_valid, reason) where is_valid is a boolean indicating
            whether the order is valid, and reason is a string explaining why
            the order is invalid (if applicable).
        """
        if not self._strategy:
            return False, "Risk management strategy not initialized"
        
        # Delegate to the selected strategy
        return self._strategy.validate_order(
            symbol=symbol,
            order_type=order_type,
            size=size,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            account_equity=account_equity
        )
    
    def update_risk_parameters(self, **params) -> None:
        """Update risk management parameters.
        
        Args:
            **params: Key-value pairs of parameters to update.
        """
        if not params:
            return
            
        # Get current config from container
        config = self._container.resolve(BotConfig)
        
        # Update config with new parameters
        for key, value in params.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        # Update the config in the container
        self._container.register_instance(BotConfig, config)
        
        # Reinitialize strategy if risk strategy changed
        if 'risk_strategy' in params:
            self._init_strategy()
            
        if self.enable_debug:
            logger.debug(f"Updated risk parameters: {params}")
        
        # Update strategy parameters
        if self._strategy:
            self._strategy.update_risk_parameters(**params)
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get a summary of the current risk settings.
        
        Returns:
            A dictionary containing risk management settings and metrics.
        """
        return {
            'risk_strategy': getattr(self.config, 'risk_strategy', 'fixed_fractional'),
            'risk_percent': getattr(self.config, 'risk_percent', 1.0),
            'lot_size': getattr(self.config, 'lot_size', 0.1),
            'min_lot_size': getattr(self.config, 'min_lot_size', 0.01),
            'max_lot_size': getattr(self.config, 'max_lot_size', 100.0),
            'max_open_positions': getattr(self.config, 'max_open_positions', 10),
            'max_exposure_percent': getattr(self.config, 'max_exposure_percent', 100.0)
        }
