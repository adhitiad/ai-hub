class CryptoAnalyst:
    def analyze(self, symbol: str, price_data: float):
        """
        Analisis On-Chain & Market Sentiment untuk Crypto
        """
        # Simulasi Data On-Chain (Nanti connect API Glassnode/CryptoQuant)
        # Logika: Exchange Inflow Tinggi = Bearish (Paus mau jual)
        # Exchange Outflow Tinggi = Bullish (Akumulasi ke wallet dingin)

        import random

        exchange_net_flow = random.uniform(-1000, 1000)  # BTC flow
        fear_greed_index = random.randint(10, 90)

        status = "NEUTRAL"
        if exchange_net_flow < -500:  # Outflow besar
            status = "ACCUMULATION"
        elif exchange_net_flow > 500:  # Inflow besar
            status = "DISTRIBUTION"

        return {
            "asset_type": "CRYPTO",
            "on_chain_status": status,
            "net_flow": f"{exchange_net_flow:.2f} BTC",
            "fear_greed": fear_greed_index,
            "signal": (
                "BUY"
                if status == "ACCUMULATION" and fear_greed_index < 30
                else "SELL" if status == "DISTRIBUTION" else "HOLD"
            ),
        }
