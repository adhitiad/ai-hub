"""
Tests for the notifier module, specifically format_signal_message.
"""
from src.core.notifier import format_signal_message

def test_format_signal_message_buy_full_fields():
    """Test format_signal_message with all fields populated for a BUY action."""
    signal_data = {
        "Action": "BUY",
        "Symbol": "BTC/USDT",
        "Price": 65000.0,
        "Tp": 67000.0,
        "Sl": 63000.0,
        "AI_Analysis": "Bullish trend detected.",
        "Confidence": "85%",
        "Timestamp": "2023-10-27T10:00:00Z"
    }

    msg = format_signal_message(signal_data)

    assert "🟢" in msg
    assert "BTC/USDT" in msg
    assert "BUY" in msg
    assert "65000.0" in msg
    assert "67000.0" in msg
    assert "63000.0" in msg
    assert "Bullish trend detected." in msg
    assert "85%" in msg
    assert "2023-10-27T10:00:00Z" in msg

def test_format_signal_message_sell_partial_fields():
    """Test format_signal_message with partial fields for a SELL action."""
    signal_data = {
        "Action": "SELL",
        "Symbol": "ETH/USDT"
    }

    msg = format_signal_message(signal_data)

    assert "🔴" in msg
    assert "ETH/USDT" in msg
    assert "SELL" in msg
    assert "N/A" in msg # Missing Price, TP, SL should fall back to N/A
    assert "Technical Signal" in msg # Default AI_Analysis
    assert "Confidence:" not in msg
    assert "Time:" not in msg

def test_format_signal_message_unknown_action():
    """Test format_signal_message with an unknown action."""
    signal_data = {
        "Action": "HOLD",
        "Symbol": "SOL/USDT"
    }

    msg = format_signal_message(signal_data)

    assert "⚪" in msg # Icon for unknown actions
    assert "HOLD" in msg
    assert "SOL/USDT" in msg

def test_format_signal_message_not_a_dict():
    """Test format_signal_message with truthy non-dict inputs and None."""
    # Truthy non-dict string
    assert format_signal_message("BUY BTC") == "Sinyal tidak valid."

    # Truthy non-dict list
    assert format_signal_message(["BUY", "BTC"]) == "Sinyal tidak valid."

    # None
    assert format_signal_message(None) == "Sinyal tidak valid."

def test_format_signal_message_empty_dict():
    """Test format_signal_message with an empty dictionary."""
    msg = format_signal_message({})

    assert "⚪" in msg
    assert "UNKNOWN" in msg # Default symbol
    assert "WAIT" in msg # Default action
    assert "N/A" in msg # Default price, tp, sl
    assert "Technical Signal" in msg
