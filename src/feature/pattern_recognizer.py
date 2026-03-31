def _detect_doji(c_body, c_range, c_lower_wick, c_upper_wick):
    if (c_body / c_range) < 0.1:
        if c_lower_wick > 3 * c_body and c_upper_wick < c_body:
            return 10, "Bullish Dragonfly Doji"
        elif c_upper_wick > 3 * c_body and c_lower_wick < c_body:
            return -10, "Bearish Gravestone Doji"
        else:
            return 0, "Neutral Doji"
    return 0, None


def _detect_hammer(c_body, c_lower_wick, c_upper_wick):
    if c_lower_wick > 2 * c_body and c_upper_wick < c_body:
        return 15, "Bullish Hammer"
    return 0, None


def _detect_shooting_star(c_body, c_lower_wick, c_upper_wick):
    if c_upper_wick > 2 * c_body and c_lower_wick < c_body:
        return -15, "Bearish Shooting Star"
    return 0, None


def _detect_engulfing(p_open, p_close, c_open, c_close):
    if (p_close < p_open) and (c_close > c_open):
        if c_close > p_open and c_open < p_close:
            return 25, "Bullish Engulfing"
    elif (p_close > p_open) and (c_close < c_open):
        if c_close < p_open and c_open > p_close:
            return -25, "Bearish Engulfing"
    return 0, None


def _detect_marubozu(c_body, c_range, c_open, c_close):
    if (c_body / c_range) > 0.9:
        if c_close > c_open:
            return 10, "Bullish Marubozu"
        else:
            return -10, "Bearish Marubozu"
    return 0, None


def detect_chart_patterns(df):
    """
    Mendeteksi pola candlestick secara manual (Native Python) tanpa dependency TA-Lib.
    Mengenali: Engulfing, Hammer, Shooting Star, Doji, Marubozu.

    Output:
        - score (int): Total skor sentimen (-100 s/d 100)
        - patterns (list): Daftar nama pola yang terdeteksi
    """
    if df.empty or len(df) < 3:
        return 0, []

    # Ambil 2 candle terakhir untuk perbandingan
    curr = df.iloc[-1]
    prev = df.iloc[-2]

    patterns = []
    score = 0

    # --- Helper Values ---
    # Current Candle
    c_open, c_high, c_low, c_close = (
        curr["Open"],
        curr["High"],
        curr["Low"],
        curr["Close"],
    )
    c_body = abs(c_close - c_open)
    c_range = c_high - c_low
    c_upper_wick = c_high - max(c_close, c_open)
    c_lower_wick = min(c_close, c_open) - c_low

    # Previous Candle
    p_open, p_close = (
        prev["Open"],
        prev["Close"],
    )

    # Hindari pembagian dengan nol
    if c_range == 0:
        c_range = 0.00001

    # ==========================
    # 1. DOJI (Indecision)
    # ==========================
    doji_score, doji_pattern = _detect_doji(c_body, c_range, c_lower_wick, c_upper_wick)
    if doji_pattern:
        score += doji_score
        patterns.append(doji_pattern)

    # ==========================
    # 2. HAMMER & HANGING MAN
    # ==========================
    elif doji_pattern is None:
        hammer_score, hammer_pattern = _detect_hammer(
            c_body, c_lower_wick, c_upper_wick
        )
        if hammer_pattern:
            score += hammer_score
            patterns.append(hammer_pattern)

        # ==========================
        # 3. SHOOTING STAR & INVERTED HAMMER
        # ==========================
        else:
            star_score, star_pattern = _detect_shooting_star(
                c_body, c_lower_wick, c_upper_wick
            )
            if star_pattern:
                score += star_score
                patterns.append(star_pattern)

    # ==========================
    # 4. ENGULFING (Kuat)
    # ==========================
    engulfing_score, engulfing_pattern = _detect_engulfing(
        p_open, p_close, c_open, c_close
    )
    if engulfing_pattern:
        score += engulfing_score
        patterns.append(engulfing_pattern)

    # ==========================
    # 5. MARUBOZU (Momentum)
    # ==========================
    marubozu_score, marubozu_pattern = _detect_marubozu(
        c_body, c_range, c_open, c_close
    )
    if marubozu_pattern:
        score += marubozu_score
        patterns.append(marubozu_pattern)

    # Clamping Score agar tetap di range -100 s/d 100
    total_score = max(min(score, 100), -100)

    return int(total_score), patterns
