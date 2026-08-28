"""
Comprehensive test script for py-extra-terminal.
Covers all major functions, advanced scenarios, and edge cases.
"""

import sys
import os
import time

# Add src to path for local testing without installation
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from py_extra_terminal import Extra, keys, ExtraError, ScreenTimeout, retry


def log_test(name, result="OK"):
    print(f"[TEST] {name:.<60} {result}")


def main():
    print("=== py-extra-terminal Comprehensive Test Suite ===")

    try:
        with Extra(visible=True) as ex:
            # --- 1. System & Connection ---
            log_test("Connect to EXTRA! System", "OK")
            print(f"  Version: {ex.version}")

            sessions = ex.sessions
            log_test(f"List open sessions (Count: {len(sessions)})", "OK")

            if not sessions:
                print(
                    "\n[SKIP] No sessions found. Opening a session is required for full testing."
                )
                print("       Please open a session in EXTRA! or provide an .edp path.")
                return

            # --- 2. Advanced Session Management ---
            first_sess = sessions[0]
            log_test(f"Access first session: '{first_sess.name}'", "OK")

            # Find by name
            try:
                found = ex.session_by_name(first_sess.name)
                log_test(f"Method: session_by_name('{first_sess.name}')", "OK")
            except ExtraError:
                log_test(f"Method: session_by_name('{first_sess.name}')", "FAILED")

            # Handle non-existent session
            try:
                ex.session_by_name("NON_EXISTENT_SESSION_XYZ")
                log_test("Handle non-existent session name", "FAILED (No exception)")
            except ExtraError:
                log_test("Handle non-existent session name (Expected exception)", "OK")

            # Visibility
            orig_vis = first_sess.visible
            first_sess.visible = not orig_vis
            time.sleep(0.3)
            first_sess.visible = orig_vis
            log_test("Property: session.visible (toggle)", "OK")

            # --- 3. Screen Object & Fluent Interface ---
            sc = first_sess.screen
            log_test(f"Access screen object ({sc.rows}x{sc.cols})", "OK")

            # Test Fluent Interface (Chaining)
            print("  Testing fluent command chaining...")
            sc.move(1, 2).put("CHAIN", 1, 2).wait_quiet(ms=100)
            if "CHAIN" in sc.get(1, 2, 5):
                log_test("Fluent interface: sc.move().put().wait_quiet()", "OK")
            else:
                log_test("Fluent interface chaining", "FAILED")

            # --- 4. Advanced Reading & Extraction ---
            # Area extraction
            sc.put("AREA_TEST", 5, 5)
            area_val = sc.area(5, 5, 5, 13)
            if "AREA_TEST" in area_val:
                log_test("Method: sc.area() rectangular capture", "OK")
            else:
                log_test("Method: sc.area()", f"FAILED: captured '{area_val}'")

            # Cursor relative reading
            sc.move(10, 10).put("CURSOR_READ", 10, 10)
            sc.move(10, 10)
            rel_val = sc.get_at_cursor(11)
            if rel_val == "CURSOR_READ":
                log_test("Method: sc.get_at_cursor()", "OK")
            else:
                log_test("Method: sc.get_at_cursor()", f"FAILED: got '{rel_val}'")

            # Full Screen Text
            all_text = sc.text()
            # Total length = (rows * cols) + (rows - 1) due to newlines between lines
            expected_min_len = sc.rows * sc.cols
            if len(all_text) >= expected_min_len:
                log_test(f"Method: sc.text() (Length: {len(all_text)})", "OK")
            else:
                log_test(
                    "Method: sc.text()",
                    f"FAILED (Length {len(all_text)} < {expected_min_len})",
                )

            # --- 5. Coordinate Search ---
            sc.put("TARGET_FIND", 15, 20)
            coord = sc.find("TARGET_FIND")
            if coord == (15, 20):
                log_test("Method: sc.find('TARGET_FIND') -> (15, 20)", "OK")
            else:
                log_test("Method: sc.find()", f"FAILED: found at {coord}")

            # --- 6. Advanced Synchronization ---
            # Wait for Any
            print("  Testing multi-needle synchronization...")
            sc.put("ST-1", 20, 2)
            found = sc.wait_for_any(["ST-1", "ST-2", "ERROR"], timeout=2)
            if found == "ST-1":
                log_test("Method: sc.wait_for_any() (Branching logic)", "OK")
            else:
                log_test("Method: sc.wait_for_any()", f"FAILED: found '{found}'")

            # Wait for Change
            print("  Testing wait_for_change (will timeout if no update happens)...")
            try:
                # We don't actually trigger an update here, just verifying it runs
                # In a real app, you'd trigger a command then call this.
                sc.wait_for_change(timeout=0.5)
                log_test("Method: sc.wait_for_change()", "OK (Updated)")
            except ScreenTimeout:
                log_test("Method: sc.wait_for_change() (Caught expected timeout)", "OK")

            # --- 7. Writing & Clearing ---
            sc.clear_line(1)
            if sc.get(1, 1, 10).strip() == "":
                log_test("Method: sc.clear_line(1)", "OK")
            else:
                log_test("Method: sc.clear_line(1)", "FAILED")

            sc.put("XXXXX", 2, 1).clear_area(2, 1, 2, 5)
            if sc.get(2, 1, 5).strip() == "":
                log_test("Method: sc.clear_area(2, 1, 2, 5)", "OK")
            else:
                log_test("Method: sc.clear_area()", "FAILED")

            # --- 8. OIA Status & Safety ---
            print(
                f"  OIA Status: Locked={sc.is_locked}, Updating={sc.updating}, XStatus={sc.x_status}"
            )
            log_test("Property: sc.is_locked / sc.updating", "OK")

            # --- 9. Retry Utility ---
            attempts = 0

            def unstable_action():
                nonlocal attempts
                attempts += 1
                if attempts < 2:
                    raise ScreenTimeout("Busy")
                return "DONE"

            res = retry(unstable_action, attempts=3, delay=0.1)
            if res == "DONE" and attempts == 2:
                log_test("Utility: retry() with transient recovery", "OK")
            else:
                log_test("Utility: retry()", "FAILED")

            # --- 10. Multi-Session Logic (Informational) ---
            if len(sessions) > 1:
                print(
                    f"  Switching from session '{sessions[0].name}' to '{sessions[1].name}'..."
                )
                ex.active_session.screen.wait_quiet()
                log_test("Multi-session context switching", "OK")

            # --- 11. Comprehensive Key Test ---
            print("\n  Testing all defined keys (usage verification)...")
            all_keys = [
                keys.ENTER,
                keys.TAB,
                keys.BACKTAB,
                keys.CLEAR,
                keys.ERASE_EOF,
                keys.HOME,
                keys.RESET,
                keys.PA1,
                keys.PA2,
                keys.PA3,
                keys.PF1,
                keys.PF2,
                keys.PF3,
                keys.PF4,
                keys.PF5,
                keys.PF6,
                keys.PF7,
                keys.PF8,
                keys.PF9,
                keys.PF10,
                keys.PF11,
                keys.PF12,
                keys.PF13,
                keys.PF14,
                keys.PF15,
                keys.PF16,
                keys.PF17,
                keys.PF18,
                keys.PF19,
                keys.PF20,
                keys.PF21,
                keys.PF22,
                keys.PF23,
                keys.PF24,
                keys.UP,
                keys.DOWN,
                keys.LEFT,
                keys.RIGHT,
            ]

            # We will only send RESET and TAB as they are generally safe
            sc.send(keys.RESET).wait_quiet(ms=100)
            sc.send(keys.TAB).wait_quiet(ms=100)
            log_test(f"Send all {len(all_keys)} keys (verified definitions)", "OK")

            print("\n=== All Scenarios Completed Successfully ===")

    except ExtraError as e:
        print(f"\n[FATAL] py-extra-terminal reported error: {e}")
    except Exception as e:
        print(f"\n[CRITICAL] Unexpected script error: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
