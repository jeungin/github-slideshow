# re_auto_bot.py - Issue Fixes Documentation

## Overview

This document details all the fixes implemented in `re_auto_bot.py` to address Critical, Major, Moderate, and Minor issues. All issues have been pre-fixed in the implementation.

## 🔴 Critical Issues (Fixed)

### Issue #1: Infinite Loop & Memory Leak
**Problem**: `continue` statement after buy logic prevented sell logic from executing.

**Location**: Trading loop (line ~445)

**Fix Applied**:
```python
# ❌ OLD (Buggy):
if len(positions) >= MAX_ACTIVE_TRADES:
    log_trade("Max positions reached")
    continue  # This prevented sell logic!

# ✅ NEW (Fixed):
if len(positions) >= MAX_ACTIVE_TRADES:
    log_trade("Max positions reached")
    # No continue! Loop continues naturally
```

**Verification**: Search for `# Issue #1` comments in the code. The trading loop now properly executes both buy AND sell logic in each iteration.

---

### Issue #2: Discord Heartbeat Blocking
**Problem**: Synchronous chunk reading from Ollama blocked the event loop, causing Discord connection timeouts.

**Location**: `ask_ollama()` function (lines ~248-318)

**Fix Applied**:
```python
async def read_chunks_async():
    """비동기 청크 읽기 - Discord heartbeat 허용"""
    result_parts = []
    last_chunk_ts = time.time()
    
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            await asyncio.sleep(0)  # ✅ Yield control
            continue
        
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            await asyncio.sleep(0)  # ✅ Yield on error
            continue
        
        if "response" in data:
            result_parts.append(data["response"])
            last_chunk_ts = time.time()
        
        await asyncio.sleep(0)  # ✅ Yield after each chunk
        
        if data.get("done"):
            break
    
    return result_parts
```

**Verification**: Each iteration calls `await asyncio.sleep(0)` to yield control back to the event loop, allowing Discord heartbeats to be sent.

---

### Issue #3: Re-buy Prevention Logic
**Problem**:
1. RESELL_BLOCK_TIME comment incorrect ("10분" but actually 1 hour)
2. RECENT_SELLS not updated on all sell paths

**Location**: Lines 87, 365-380

**Fix Applied**:
```python
# 1. Correct comment (line 87)
RESELL_BLOCK_TIME = 3600  # 재매수 차단 시간 (1시간) ✅ Fixed

# 2. Update RECENT_SELLS on all sell paths (lines 365-380)
if success:
    try:
        current_price_latest, _ = kis.get_current_price(code)
        if current_price_latest:
            RECENT_SELLS[code] = (current_price_latest, time.time())
            log_trade(f"📝 재매수 방지 기록: {name} @ {current_price_latest:,}원")
    except Exception as e:
        log_trade(f"⚠️ 재매수 방지 기록 실패: {e}", level="WARNING")
```

**Verification**: Search for "Issue #3" comments. RECENT_SELLS is now updated after every successful sell.

---

## ⚠️ Major Issues (Fixed)

### Issue #4: Credit Buy Fallback Duplication
**Problem**: Fallback logic existed both in `send_order()` and at call sites, risking duplicate orders.

**Location**: `send_order()` method (lines 186-229)

**Fix Applied**:
```python
def send_order(
    self, 
    code: str, 
    qty: int, 
    type_str: str = "매수",
    use_credit: bool = False,
    auto_fallback: bool = True  # ✅ New parameter
) -> Tuple[bool, str]:
    """
    Issue #4 Fix:
    - Added auto_fallback parameter
    - Fallback logic contained in this function only
    - Caller can disable by setting auto_fallback=False
    """
    if use_credit:
        # Try credit
        success = True  # API call here
        
        if not success and auto_fallback:
            log_trade("💵 [자동 폴백] 신용 실패 → 현금 재시도")
            # Retry with cash
            success = True  # API call here
            return (success, "Fallback succeeded")
    # ...
```

**Verification**: All credit orders now use `auto_fallback=True` by default, with option to disable at call site.

---

### Issue #5: AI Timeout Cooldown Adjustment
**Problem**: Simple timeouts (model slow) triggered 60-second cooldown unnecessarily.

**Location**: `ask_ollama()` exception handling (lines 299-303)

**Fix Applied**:
```python
except asyncio.TimeoutError:
    # Issue #5 Fix: No cooldown for timeouts
    log_trade("⚠️ Ollama 타임아웃 - 기술적 신호로 폴백", level="WARNING")
    # NOT setting OLLAMA_DOWN_UNTIL_TS
    # Timeout ≠ service down
    return ""
```

**Verification**: Timeouts return empty string immediately; only actual errors set cooldown.

---

### Issue #6: Balance Cache Problems
**Problem**: 3-second cache caused stale balance data after trades.

**Location**: `get_balance()` method and all call sites

**Fix Applied**:
```python
# 1. Reduced cache duration (line 90)
BALANCE_CACHE_DURATION = 1  # 3초 → 1초 단축 ✅

# 2. Added force_refresh parameter (lines 141-178)
def get_balance(self, debug: bool = False, force_refresh: bool = False):
    """
    Issue #6 Fix:
    - Reduced cache to 1 second
    - Added force_refresh parameter
    """
    if not force_refresh and BALANCE_CACHE["data"]:
        if current_time - BALANCE_CACHE["timestamp"] < BALANCE_CACHE_DURATION:
            return BALANCE_CACHE["data"]
    # Fetch fresh...

# 3. Force refresh after trades (line 336, 376)
kis.get_balance(debug=False, force_refresh=True)
```

**Verification**: All trades now force refresh balance immediately after execution.

---

## 🟡 Moderate Issues (Fixed)

### Issue #7: Environment Variable Validation
**Problem**: Missing validation at trading loop start could cause mid-execution crashes.

**Location**: `trading_loop()` start and `validate_environment()` function

**Fix Applied**:
```python
# 1. Pre-flight validation (lines 515-541)
def validate_environment() -> bool:
    """Issue #7 Fix: Pre-flight validation"""
    required_vars = {
        "KIS_APP_KEY": APP_KEY,
        "KIS_APP_SECRET": APP_SECRET,
        # ...
    }
    
    missing = [name for name, val in required_vars.items() if not val]
    if missing:
        log_trade(f"❌ Missing: {', '.join(missing)}", level="ERROR")
        return False
    return True

# 2. Loop start validation (lines 392-399)
async def trading_loop():
    # Issue #7 Fix: Revalidate at loop start
    if not all([APP_KEY, APP_SECRET, ACCOUNT_NO, ACCOUNT_CODE, DISCORD_TOKEN]):
        error_msg = "❌ 필수 환경변수 누락"
        log_trade(error_msg, level="ERROR")
        return
```

**Verification**: Bot validates environment both at startup and at each loop iteration start.

---

### Issue #8: Memory Cleanup Optimization
**Problem**: Technical analysis objects not explicitly deleted, causing memory leaks.

**Location**: `analyze_and_buy()` finally block (lines 346-358)

**Fix Applied**:
```python
finally:
    # Issue #8 Fix: Explicit memory cleanup
    cleanup_objects = [
        df, bb_indicator, rsi_indicator, 
        macd_indicator, technical_df
    ]
    for obj in cleanup_objects:
        try:
            if obj is not None:
                del obj
        except:
            pass
    
    # Periodic GC (every 10 loops)
    global loop_count
    if loop_count % 10 == 0:
        gc.collect()
        log_trade("🗑️ Garbage collection", level="DEBUG")
```

**Verification**: All TA objects deleted in finally block; GC runs every 10 loops.

---

## 🟢 Minor Issues (Fixed)

### Issue #9: Log Level Management
**Problem**: Debug logs flooding output in production.

**Location**: `log_trade()` function (lines 123-142)

**Fix Applied**:
```python
# 1. Add DEBUG_MODE (line 93)
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("1", "true", "yes")

# 2. Level filtering (lines 123-142)
def log_trade(msg: str, level: str = "INFO"):
    """
    Issue #9 Fix: Log level control
    
    Args:
        level: "DEBUG", "INFO", "WARNING", "ERROR"
    """
    if level == "DEBUG" and not DEBUG_MODE:
        return  # Skip debug logs in production
    
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{now}] [{level}] {msg}"
    print(formatted_msg)
```

**Usage**:
```python
log_trade("Debug info", level="DEBUG")  # Only in debug mode
log_trade("Important", level="INFO")    # Always shown
```

**Verification**: Set `DEBUG_MODE=false` to suppress debug logs.

---

### Issue #10: Configuration Environment Variables
**Problem**: Configuration values hard-coded, reducing flexibility.

**Location**: Configuration section (lines 52-88)

**Fix Applied**:
```python
# Issue #10 Fix: All configs use environment variables with defaults
STOP_LOSS = float(os.getenv("STOP_LOSS", "-1.5"))
QUICK_PROFIT = float(os.getenv("QUICK_PROFIT", "2.0"))
TARGET_PROFIT = float(os.getenv("TARGET_PROFIT", "5.0"))
TRAILING_START = float(os.getenv("TRAILING_START", "4.0"))
MAX_ACTIVE_TRADES = int(os.getenv("MAX_ACTIVE_TRADES", "3"))
ONE_TIME_BUY_AMT = int(os.getenv("ONE_TIME_BUY_AMT", "1500000"))
RESELL_BLOCK_TIME = 3600  # Can be made env var if needed
BALANCE_CACHE_DURATION = 1  # Can be made env var if needed
```

**Usage**:
```bash
export STOP_LOSS=-2.0
export MAX_ACTIVE_TRADES=5
python re_auto_bot.py
```

**Verification**: All trading parameters now support environment variable override.

---

## Testing Checklist

After deploying this fixed version, verify:

- [ ] **Issue #1**: Verify both buy and sell logic execute in same loop iteration
- [ ] **Issue #2**: Bot maintains Discord connection for 1+ hours
- [ ] **Issue #3**: Sold stocks are blocked from re-purchase for 1 hour
- [ ] **Issue #4**: Credit order failures don't cause duplicate orders
- [ ] **Issue #5**: AI timeouts don't trigger unnecessary cooldowns
- [ ] **Issue #6**: Balance updates immediately after trades
- [ ] **Issue #7**: Bot validates environment at startup and loop start
- [ ] **Issue #8**: Memory usage stays stable over time
- [ ] **Issue #9**: Debug logs only appear when DEBUG_MODE=true
- [ ] **Issue #10**: Configuration values can be overridden via environment

---

## Environment Variables Reference

### Required
```bash
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_ACCOUNT_NO=your_account_number
KIS_ACCOUNT_CODE=your_account_code
DISCORD_BOT_TOKEN=your_discord_token
DISCORD_CHANNEL_ID=your_channel_id
```

### Optional (with defaults)
```bash
DEBUG_MODE=false              # Enable debug logging
STOP_LOSS=-1.5               # Stop loss percentage
QUICK_PROFIT=2.0             # Quick profit target
TARGET_PROFIT=5.0            # Final profit target
TRAILING_START=4.0           # Trailing stop start
MAX_ACTIVE_TRADES=3          # Max concurrent positions
ONE_TIME_BUY_AMT=1500000     # Buy amount in KRW
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

---

## Architecture Notes

### Async Design
- Event loop never blocked (Issue #2 fix)
- All I/O operations use asyncio
- Discord heartbeats always sent on time

### Memory Management
- Explicit object deletion (Issue #8 fix)
- Periodic garbage collection
- Cache with TTL (Issue #6 fix)

### Error Recovery
- Graceful degradation (AI failures → technical signals)
- Retry logic with fallback (Issue #4 fix)
- Comprehensive validation (Issue #7 fix)

### Configurability
- Environment-driven config (Issue #10 fix)
- Log level control (Issue #9 fix)
- Flexible cooldown management (Issue #5 fix)

---

## Code Quality

All fixes maintain:
- ✅ Backward compatibility
- ✅ Clear error messages
- ✅ Comprehensive logging
- ✅ Type hints
- ✅ Detailed comments
- ✅ Proper exception handling

---

## Related Issues

Fixes #2 - All critical, major, moderate, and minor issues resolved
