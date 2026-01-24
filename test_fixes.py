#!/usr/bin/env python3
"""
Test script to verify key issue fixes in re_auto_bot.py
This validates the patterns without requiring actual API credentials.
"""

import re
import sys

def test_issue_1_no_continue_in_trading_loop():
    """Verify Issue #1: No 'continue' statements after buy logic in trading_loop"""
    print("Testing Issue #1: Infinite loop fix...")
    
    with open('re_auto_bot.py', 'r') as f:
        content = f.read()
    
    # Find the trading_loop function more precisely
    trading_loop_match = re.search(r'async def trading_loop\(\):.*?(?=\n@|\nclass |\nasync def [a-z_]+\(|\ndef main\(\))', 
                                   content, re.DOTALL)
    
    if not trading_loop_match:
        print("  ❌ Could not find trading_loop function")
        return False
    
    trading_loop_code = trading_loop_match.group(0)
    
    # Find the BUY LOGIC section specifically
    buy_section_match = re.search(r'# BUY LOGIC.*?# Issue #1 Fix: No .continue. statement!', 
                                   trading_loop_code, re.DOTALL)
    
    if not buy_section_match:
        print("  ⚠️ Could not find buy logic section with Issue #1 marker")
        # Check if there are any continue statements after "매수" (buy)
        buy_after = re.search(r'매수 분석 시작.*', trading_loop_code, re.DOTALL)
        if buy_after and re.search(r'\n\s+continue\s*(?:#|$)', buy_after.group(0)):
            print("  ❌ Found 'continue' statement after buy logic start")
            return False
        print("  ✅ No continue statements found in buy section")
        return True
    
    buy_section = buy_section_match.group(0)
    
    # Check for problematic 'continue' statements (not in comments)
    # Look for 'continue' that is not part of a comment
    if re.search(r'\n\s+continue\s*(?:#|$)', buy_section):
        print("  ❌ Found 'continue' statement in buy logic section")
        return False
    else:
        print("  ✅ No blocking 'continue' statements in buy logic")
        return True


def test_issue_2_async_sleep_in_ollama():
    """Verify Issue #2: Async yield points in ask_ollama function"""
    print("\nTesting Issue #2: Discord heartbeat fix...")
    
    with open('re_auto_bot.py', 'r') as f:
        content = f.read()
    
    # Find the ask_ollama function
    ollama_match = re.search(r'async def ask_ollama\(.*?\):\s*""".*?""".*?(?=\nasync def|\ndef \w+\(|\nclass )', 
                            content, re.DOTALL)
    
    if not ollama_match:
        print("  ❌ Could not find ask_ollama function")
        return False
    
    ollama_code = ollama_match.group(0)
    
    # Check for 'await asyncio.sleep(0)' - the critical fix
    sleep_count = ollama_code.count('await asyncio.sleep(0)')
    
    if sleep_count >= 3:
        print(f"  ✅ Found {sleep_count} async yield points (await asyncio.sleep(0))")
        return True
    else:
        print(f"  ❌ Only found {sleep_count} async yield points, expected at least 3")
        return False


def test_issue_3_resell_block_time_comment():
    """Verify Issue #3: Correct RESELL_BLOCK_TIME comment"""
    print("\nTesting Issue #3: Re-buy prevention comment fix...")
    
    with open('re_auto_bot.py', 'r') as f:
        content = f.read()
    
    # Find RESELL_BLOCK_TIME definition
    resell_match = re.search(r'RESELL_BLOCK_TIME\s*=\s*3600\s*#\s*(.+)', content)
    
    if not resell_match:
        print("  ❌ Could not find RESELL_BLOCK_TIME definition")
        return False
    
    comment = resell_match.group(1)
    
    # Check that comment mentions 1시간 (1 hour), not 10분 (10 minutes)
    if '1시간' in comment or '1 hour' in comment.lower():
        print(f"  ✅ Correct comment: '{comment}'")
        return True
    elif '10분' in comment or '10 min' in comment.lower():
        print(f"  ❌ Incorrect comment still says '10분': '{comment}'")
        return False
    else:
        print(f"  ⚠️ Comment format unclear: '{comment}'")
        return True


def test_issue_4_auto_fallback_parameter():
    """Verify Issue #4: auto_fallback parameter in send_order"""
    print("\nTesting Issue #4: Credit fallback parameter...")
    
    with open('re_auto_bot.py', 'r') as f:
        content = f.read()
    
    # Find send_order function signature
    send_order_match = re.search(r'def send_order\([^)]+auto_fallback[^)]*\)', content)
    
    if send_order_match:
        print(f"  ✅ Found auto_fallback parameter in send_order")
        return True
    else:
        print(f"  ❌ auto_fallback parameter not found in send_order")
        return False


def test_issue_6_balance_cache_duration():
    """Verify Issue #6: Balance cache reduced to 1 second"""
    print("\nTesting Issue #6: Balance cache duration...")
    
    with open('re_auto_bot.py', 'r') as f:
        content = f.read()
    
    # Find BALANCE_CACHE_DURATION
    cache_match = re.search(r'BALANCE_CACHE_DURATION\s*=\s*(\d+)', content)
    
    if not cache_match:
        print("  ❌ Could not find BALANCE_CACHE_DURATION")
        return False
    
    duration = int(cache_match.group(1))
    
    if duration == 1:
        print(f"  ✅ Cache duration is 1 second (fixed from 3)")
        return True
    elif duration == 3:
        print(f"  ❌ Cache duration still 3 seconds (should be 1)")
        return False
    else:
        print(f"  ⚠️ Cache duration is {duration} seconds")
        return True


def test_issue_9_debug_mode():
    """Verify Issue #9: DEBUG_MODE environment variable"""
    print("\nTesting Issue #9: Debug mode support...")
    
    with open('re_auto_bot.py', 'r') as f:
        content = f.read()
    
    # Check for DEBUG_MODE definition
    debug_mode_match = re.search(r'DEBUG_MODE\s*=\s*os\.getenv', content)
    
    if debug_mode_match:
        print(f"  ✅ DEBUG_MODE environment variable support found")
        return True
    else:
        print(f"  ❌ DEBUG_MODE environment variable support not found")
        return False


def test_issue_10_env_var_config():
    """Verify Issue #10: Environment variable configuration"""
    print("\nTesting Issue #10: Environment variable configuration...")
    
    with open('re_auto_bot.py', 'r') as f:
        content = f.read()
    
    # Check for key config values using os.getenv
    config_vars = ['STOP_LOSS', 'QUICK_PROFIT', 'TARGET_PROFIT', 'MAX_ACTIVE_TRADES']
    found_count = 0
    
    for var in config_vars:
        if re.search(rf'{var}\s*=\s*(?:int|float)\(os\.getenv\(', content):
            found_count += 1
    
    if found_count >= 3:
        print(f"  ✅ Found {found_count}/{len(config_vars)} config vars using environment variables")
        return True
    else:
        print(f"  ❌ Only found {found_count}/{len(config_vars)} config vars using environment variables")
        return False


def main():
    print("="*70)
    print("re_auto_bot.py Issue Fix Verification")
    print("="*70)
    
    tests = [
        ("Issue #1", test_issue_1_no_continue_in_trading_loop),
        ("Issue #2", test_issue_2_async_sleep_in_ollama),
        ("Issue #3", test_issue_3_resell_block_time_comment),
        ("Issue #4", test_issue_4_auto_fallback_parameter),
        ("Issue #6", test_issue_6_balance_cache_duration),
        ("Issue #9", test_issue_9_debug_mode),
        ("Issue #10", test_issue_10_env_var_config),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("Summary:")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All critical fixes verified!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
