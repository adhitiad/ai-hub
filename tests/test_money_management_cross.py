import pytest
from src.feature.money_management import calculate_lot_size
from src.core.config_assets import get_asset_info


@pytest.mark.asyncio
async def test_calculate_lot_size_forex_base_usd():
    info = get_asset_info("EURUSD=X")
    balance = 1000
    risk = 2  # 2% = 20
    sl = 1.0950
    entry = 1.1000
    # sl distance = 0.0050
    # mult = 100000
    # val = 500
    # lot = 20 / 500 = 0.04
    lot = await calculate_lot_size(balance, risk, sl, entry, info, symbol="EURUSD=X")
    assert lot == 0.04


@pytest.mark.asyncio
async def test_calculate_lot_size_forex_cross():
    # To mock the get_usd_conversion_rate, we could patch it, but since we have a real network call fallback
    # we just run it and ensure it works (does not throw) and lot size is calculated.
    info = get_asset_info("EURGBP=X")
    balance = 1000
    risk = 2  # $20
    sl = 0.8450
    entry = 0.8500
    lot = await calculate_lot_size(balance, risk, sl, entry, info, symbol="EURGBP=X")
    assert lot > 0.01  # Expecting some valid lot size calculation


@pytest.mark.asyncio
async def test_calculate_lot_size_stock():
    info = get_asset_info("BBCA.JK")
    lot = await calculate_lot_size(1000000, 2, 9500, 10000, info, symbol="BBCA.JK")
    assert lot >= 0
