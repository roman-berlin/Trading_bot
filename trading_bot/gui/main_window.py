"""
Main window for the trading bot GUI.

This module defines the main application window with tabs for different
functionality (trading, backtesting, settings, etc.).
"""
import logging
from typing import Dict, Any, Optional, Type, Union

from PyQt5.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QMessageBox,
    QLineEdit,
    QTextEdit,
    QFileDialog,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread

from ..interfaces import IStrategy, IBroker, IRiskManager
from trading_bot.broker_factory import BrokerFactory
from ..config import BotConfig
from ..app import TradingBot, setup_container

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """Defines the signals available from a running worker thread."""
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    finished = pyqtSignal()


class TradingWorker(QObject):
    """Worker thread for running the trading bot."""
    
    def __init__(self, config: BotConfig, broker_type: str = 'mt5'):
        super().__init__()
        self.config = config
        self.broker_type = broker_type
        self.bot = None
        self.signals = WorkerSignals()
        self._is_running = False
    
    def run(self):
        """Run the trading bot in a separate thread."""
        try:
            self._is_running = True
            # Create a lightweight args namespace to configure the container
            class Args:
                symbol = self.config.symbol
                broker = self.broker_type
                debug = self.config.enable_debug

            # Build container using the same setup function as CLI
            container = setup_container(Args())
            self.bot = TradingBot(container)
            if self.bot.initialize():
                self.bot.running = True
                self.bot.run()
            self.signals.finished.emit()
        except Exception as e:
            logger.exception("Error in trading worker")
            self.signals.error.emit(str(e))
        finally:
            self._is_running = False
    
    def stop(self):
        """Stop the trading bot."""
        if self.bot is not None:
            self.bot.running = False


class StrategyConfigWidget(QWidget):
    """Widget for configuring strategy parameters."""
    
    def __init__(self, config: BotConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Strategy selection
        strategy_group = QGroupBox("Strategy Configuration")
        form_layout = QFormLayout()
        
        # Strategy selection combo box
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItem("Distance/Time Breakout", "distance_time")
        # Add more strategies here as they are implemented
        
        form_layout.addRow("Strategy:", self.strategy_combo)
        
        # Strategy parameters
        self.param_widgets = {}
        
        # Distance/Time parameters
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.1, 1000.0)
        self.distance_spin.setValue(self.config.distance_pips)
        self.distance_spin.setSuffix(" pips")
        self.param_widgets['distance_pips'] = self.distance_spin
        
        self.time_spin = QSpinBox()
        self.time_spin.setRange(1, 3600)
        self.time_spin.setValue(self.config.time_seconds)
        self.time_spin.setSuffix(" seconds")
        self.param_widgets['time_seconds'] = self.time_spin
        
        # Add parameter widgets to form
        form_layout.addRow("Distance:", self.distance_spin)
        form_layout.addRow("Time window:", self.time_spin)
        
        # Connect strategy change signal
        self.strategy_combo.currentIndexChanged.connect(self.on_strategy_changed)
        
        strategy_group.setLayout(form_layout)
        layout.addWidget(strategy_group)
        
        # Risk management group
        risk_group = QGroupBox("Risk Management")
        risk_layout = QFormLayout()
        
        # Lot size
        self.lot_size_spin = QDoubleSpinBox()
        self.lot_size_spin.setRange(0.01, 100.0)
        self.lot_size_spin.setValue(self.config.lot_size)
        self.lot_size_spin.setSingleStep(0.01)
        self.param_widgets['lot_size'] = self.lot_size_spin
        
        # Money management
        self.mm_spin = QDoubleSpinBox()
        self.mm_spin.setRange(0.0, 10.0)
        self.mm_spin.setValue(self.config.mm)
        self.mm_spin.setSingleStep(0.1)
        self.param_widgets['mm'] = self.mm_spin
        
        # Max lot size
        self.mm_max_lot_spin = QDoubleSpinBox()
        self.mm_max_lot_spin.setRange(0.01, 100.0)
        # Use max_lot_size from configuration instead of the non‑existent mm_max_lot
        self.mm_max_lot_spin.setValue(getattr(self.config, 'max_lot_size', self.config.max_lot_size))
        self.mm_max_lot_spin.setSingleStep(0.1)
        self.param_widgets['max_lot_size'] = self.mm_max_lot_spin
        
        # Stop loss and take profit
        self.sl_spin = QDoubleSpinBox()
        self.sl_spin.setRange(0, 1000)
        self.sl_spin.setValue(self.config.stop_loss_pips)
        self.sl_spin.setSuffix(" pips")
        self.param_widgets['stop_loss_pips'] = self.sl_spin
        
        self.tp_spin = QDoubleSpinBox()
        self.tp_spin.setRange(0, 1000)
        self.tp_spin.setValue(self.config.take_profit_pips)
        self.tp_spin.setSuffix(" pips")
        self.param_widgets['take_profit_pips'] = self.tp_spin
        
        # Trailing stop
        self.ts_spin = QDoubleSpinBox()
        self.ts_spin.setRange(0, 1000)
        self.ts_spin.setValue(self.config.trailing_stop)
        self.ts_spin.setSuffix(" pips")
        self.param_widgets['trailing_stop'] = self.ts_spin
        
        # Add widgets to risk layout
        risk_layout.addRow("Fixed lot size:", self.lot_size_spin)
        risk_layout.addRow("MM coefficient:", self.mm_spin)
        risk_layout.addRow("Max MM lot size:", self.mm_max_lot_spin)
        risk_layout.addRow("Stop loss:", self.sl_spin)
        risk_layout.addRow("Take profit:", self.tp_spin)
        risk_layout.addRow("Trailing stop:", self.ts_spin)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        # Symbol selection
        symbol_group = QGroupBox("Symbol")
        symbol_layout = QHBoxLayout()
        
        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)
        self.symbol_combo.addItem("EURUSD")
        self.symbol_combo.addItem("GBPUSD")
        self.symbol_combo.addItem("USDJPY")
        self.symbol_combo.addItem("AUDUSD")
        self.symbol_combo.addItem("USDCAD")
        self.symbol_combo.setCurrentText(self.config.symbol)
        
        symbol_layout.addWidget(QLabel("Symbol:"))
        symbol_layout.addWidget(self.symbol_combo)
        symbol_group.setLayout(symbol_layout)
        layout.addWidget(symbol_group)
        
        # Debug mode
        self.debug_check = QCheckBox("Enable debug mode")
        self.debug_check.setChecked(self.config.enable_debug)
        self.param_widgets['enable_debug'] = self.debug_check
        layout.addWidget(self.debug_check)
        
        # Stretch to push everything to the top
        layout.addStretch()
        
        self.setLayout(layout)
    
    def on_strategy_changed(self, index: int):
        """Handle strategy selection change."""
        strategy_name = self.strategy_combo.currentData()
        # Update UI based on selected strategy
        # For now, we only have one strategy
        pass
    
    def get_config(self) -> BotConfig:
        """Get the current configuration from the UI."""
        # Create a new config with updated values
        config = BotConfig(
            symbol=self.symbol_combo.currentText(),
            distance_pips=self.distance_spin.value(),
            time_seconds=self.time_spin.value(),
            lot_size=self.lot_size_spin.value(),
            mm=self.mm_spin.value(),
            max_lot_size=self.mm_max_lot_spin.value(),
            stop_loss_pips=self.sl_spin.value(),
            take_profit_pips=self.tp_spin.value(),
            trailing_stop=self.ts_spin.value(),
            enable_debug=self.debug_check.isChecked(),
        )
        return config


class TradingTab(QWidget):
    """Tab for controlling the trading bot."""
    
    def __init__(self, config: BotConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.worker = None
        self.worker_thread = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Status display
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Start/Stop button
        self.start_button = QPushButton("Start Trading")
        self.start_button.clicked.connect(self.toggle_trading)
        
        # Add widgets to layout
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        self.setLayout(layout)
    
    def toggle_trading(self):
        """Start or stop the trading bot."""
        if self.worker is None or not self.worker._is_running:
            self.start_trading()
        else:
            self.stop_trading()
    
    def start_trading(self):
        """Start the trading bot in a separate thread."""
        if self.worker is not None and self.worker._is_running:
            return
        
        # Update UI
        self.start_button.setText("Stop Trading")
        self.status_label.setText("Status: Starting...")
        
        # Create worker and thread
        self.worker = TradingWorker(self.config)
        self.worker_thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.signals.finished.connect(self.worker_thread.quit)
        self.worker.signals.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.signals.error.connect(self.on_error)
        
        # Start the thread
        self.worker_thread.start()
        
        # Update status after a short delay to allow thread to start
        QTimer.singleShot(500, self.update_status)
    
    def stop_trading(self):
        """Stop the trading bot."""
        if self.worker is not None:
            self.worker.stop()
            self.status_label.setText("Status: Stopping...")
            self.start_button.setEnabled(False)
    
    def update_status(self):
        """Update the status label based on worker state."""
        if self.worker is not None and self.worker._is_running:
            self.status_label.setText("Status: Running")
            self.start_button.setEnabled(True)
        else:
            self.status_label.setText("Status: Stopped")
            self.start_button.setText("Start Trading")
            self.start_button.setEnabled(True)
    
    def on_error(self, message: str):
        """Handle errors from the worker thread."""
        QMessageBox.critical(self, "Error", f"An error occurred: {message}")
        self.status_label.setText("Status: Error")
        self.start_button.setText("Start Trading")
        self.start_button.setEnabled(True)


class BacktestTab(QWidget):
    """Tab for running backtests."""
    
    def __init__(self, config: BotConfig, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        
        # Backtest controls
        controls_layout = QHBoxLayout()
        
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Select CSV file...")
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_file)
        
        self.run_button = QPushButton("Run Backtest")
        self.run_button.clicked.connect(self.run_backtest)
        
        controls_layout.addWidget(QLabel("Data file:"))
        controls_layout.addWidget(self.file_edit, 1)
        controls_layout.addWidget(self.browse_button)
        controls_layout.addWidget(self.run_button)
        
        # Results area
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        
        # Add widgets to layout
        layout.addLayout(controls_layout)
        layout.addWidget(self.results_text)
        
        self.setLayout(layout)
    
    def browse_file(self):
        """Open a file dialog to select a CSV file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_name:
            self.file_edit.setText(file_name)
    
    def run_backtest(self):
        """Run a backtest with the selected file."""
        file_name = self.file_edit.text()
        if not file_name:
            QMessageBox.warning(self, "Warning", "Please select a CSV file")
            return
        try:
            # Run the backtest and display results
            from trading_bot.backtester import run_backtest
            self.results_text.clear()
            self.results_text.append(f"Running backtest on {file_name}...")
            trades = run_backtest(file_name, self.config)
            self.results_text.append(f"Backtest complete!\n")
            self.results_text.append(f"Trades: {len(trades)}")
            # Optionally list trades
            for i, trade in enumerate(trades, start=1):
                self.results_text.append(
                    f"{i}. {trade.direction.upper()} @ {trade.entry_price} lot={trade.lot} SL={trade.sl} TP={trade.tp}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backtest failed: {str(e)}")
    
    def finish_backtest(self):
        """Called when backtest is complete."""
        self.results_text.append("Backtest complete!")
        self.results_text.append("Results:")
        self.results_text.append("  - Trades: 10")
        self.results_text.append("  - Win rate: 60%")
        self.results_text.append("  - Profit factor: 1.5")


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, config: BotConfig):
        super().__init__()
        self.config = config
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("Trading Bot")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Left panel - configuration
        config_panel = QWidget()
        config_layout = QVBoxLayout()
        
        self.strategy_config = StrategyConfigWidget(self.config)
        config_layout.addWidget(self.strategy_config)
        
        # Save button
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self.save_settings)
        config_layout.addWidget(save_button)
        
        config_panel.setLayout(config_layout)
        config_panel.setMaximumWidth(400)
        
        # Right panel - tabs
        tab_widget = QTabWidget()
        
        # Trading tab
        trading_tab = TradingTab(self.config)
        tab_widget.addTab(trading_tab, "Trading")
        
        # Backtest tab
        backtest_tab = BacktestTab(self.config)
        tab_widget.addTab(backtest_tab, "Backtest")
        
        # Add widgets to main layout
        main_layout.addWidget(config_panel)
        main_layout.addWidget(tab_widget, 1)  # Give more space to tabs
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def save_settings(self):
        """Save the current settings."""
        self.config = self.strategy_config.get_config()
        self.statusBar().showMessage("Settings saved", 3000)  # Show for 3 seconds
    
    def closeEvent(self, event):
        """Handle window close event."""
        # TODO: Clean up any running threads or connections
        event.accept()
