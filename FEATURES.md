# py-extra-terminal Capabilities

The `py-extra-terminal` framework is designed for high-performance, robust automation of Attachmate EXTRA! X-treme terminal emulators. It wraps the COM/OLE Automation interface into a clean, Pythonic API.

## 1. Connection & Session Management
- **Automatic Lifecycle**: Uses Python context managers (`with Extra() as ex:`) to ensure COM resources are initialized and uninitialized correctly.
- **Multi-Session Support**: Simultaneously manage multiple `.edp` session profiles.
- **Session Discovery**: Find sessions by name or list all currently open terminal windows.
- **Visibility Control**: Programmatically hide or show terminal windows for background automation or interactive debugging.

## 2. Advanced Screen Reading
- **Flexible Reading**: Read specific strings with `get(row, col, length)`.
- **Coordinate-Free Reading**: Use `get_at_cursor(length)` to read where the terminal is currently focused.
- **Area Extraction**: Capture rectangular blocks of text with `area(r1, c1, r2, c2)`.
- **Full Screen Dumps**: Get the entire screen as a list of strings (`dump()`) or a single newline-separated string (`text()`).
- **Coordinate Search**: Find the `(row, col)` position of any text string on the screen using `find(needle)`.

## 3. Precision Screen Writing
- **Fluent Interface**: Methods like `move()`, `put()`, and `send()` return the `Screen` object, allowing for elegant method chaining.
- **Coordinate-Based Writing**: Place text exactly where needed with `put(text, row, col)`.
- **Cursor-Relative Writing**: Output text at the current cursor position with `put_at_cursor(text)`.
- **Automated Entry**: Use `enter(text, row, col)` to write text and send an `<Enter>` signal in one atomic operation.

## 4. Advanced Synchronization
- **Host Quietness**: `wait_quiet()` intelligently waits for host-terminal traffic to stop, ensuring the screen is ready for the next command.
- **Content-Based Waiting**: `wait_for("STRING")` pauses execution until specific text appears.
- **Multi-State Waiting**: `wait_for_any(["SUCCESS", "ERROR"])` allows branching logic by returning which of several possible strings appeared first.
- **Change Detection**: `wait_for_change()` detects when the host has updated any part of the screen.
- **Cursor Tracking**: `wait_for_cursor(row, col)` synchronizes with host-side cursor movements.

## 5. Robustness & Utilities
- **Retry Mechanism**: The built-in `retry()` decorator/utility handles transient network or host delays with configurable attempts and delays.
- **OIA Integration**: Real-time access to the Operator Information Area (OIA) to check for keyboard inhibits or system busy states via `is_locked`.
- **Type Safety**: Full type hinting support for modern IDEs and static analysis.
- **Legacy Compatibility**: Intelligent fallbacks for different versions of EXTRA! X-treme COM objects.

## 6. Comprehensive Keys Library
- **Pre-defined Constants**: Access all terminal-specific keys like `keys.PF1` through `keys.PF24`, `keys.ENTER`, `keys.CLEAR`, `keys.PA1`, and directional arrows.
