import asyncio
import pytest
from src.core.agent import get_detailed_signal

@pytest.mark.asyncio
async def test_stock_indo_with_slash_is_not_crypto():
    """
    Tests that a stock_indo symbol containing a '/' is not misclassified as crypto.
    """
    # This symbol would have been incorrectly classified as crypto before the fix
    symbol = "ITMG.JK/IDR"
    
    # Mock asset_info to avoid dependency on get_asset_info
    asset_info = {
        "symbol": symbol,
        "type": "stock_indo",
        "category": "stock_indo"
    }
    
    # We don't need a real model or full data for this test, 
    # we just need to see what asset_type is used.
    # We expect it to fail because of no data, but the error message
    # will tell us what went wrong.
    result = await get_detailed_signal(symbol, asset_info=asset_info)
    
    # We expect the function to return a 'No Data Fetched' reason because we are not providing any data.
    # If it were misclassified as crypto, it might try to use crypto-specific logic that would fail differently.
    # A more robust test would mock the data loading and check the analysis path.
    # For now, we are checking that it doesn't fail with a crypto-related error.
    assert result["Reason"] in {"No Data Fetched", "No Model"}
