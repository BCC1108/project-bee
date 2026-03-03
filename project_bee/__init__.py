"""
Project BEE - Cryptocurrency Trading & Backtesting Framework
"""

__version__ = "0.1.0"
__author__ = "baronfkingCEE"

try:
    from .core.strategy import Strategy
    __all__ = ['Strategy']
except ImportError:
    __all__ = []
