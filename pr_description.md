🧹 [code health improvement] Refactor `detect_chart_patterns` in `pattern_recognizer.py`

🎯 **What:**
The `detect_chart_patterns` function in `src/feature/pattern_recognizer.py` had high function complexity as it handled multiple sub-pattern logic flows (Doji, Hammer, Shooting Star, Engulfing, Marubozu) in a single block. This PR extracts the specific logic for each pattern into private helper functions (`_detect_doji`, `_detect_hammer`, `_detect_shooting_star`, `_detect_engulfing`, `_detect_marubozu`), reducing the cyclomatic complexity of the main loop. Additionally, unused variables (`p_high`, `p_low`) and unused imports (`pandas`) have been cleaned up, and the file was formatted with `black`.

💡 **Why:**
Splitting long functions and isolating sub-patterns into smaller helper functions drastically improves code readability and maintainability. It makes it easier to test individual candlestick patterns in isolation in the future, and makes the main aggregation function more declarative and easier to follow without deep-diving into the math logic of individual patterns. Removing unused variables/imports improves namespace cleanliness and reduces linter noise.

✅ **Verification:**
- Wrote and ran manual comparison tests that execute both the original `detect_chart_patterns` function and the refactored version over 5 distinct test cases (capturing dragonfly doji, bullish hammer, bearish shooting star, bearish engulfing, and bearish marubozu scenarios).
- Verified that the refactored logic returned the *exact* same score integer and pattern list as the original code for all test cases.
- Ran `black` for formatting and `ruff check` to ensure zero linter errors/warnings.

✨ **Result:**
Reduced cyclomatic complexity and line length inside `detect_chart_patterns` without breaking or altering functionality. Increased overall maintainability and clean structure in `pattern_recognizer.py`.
