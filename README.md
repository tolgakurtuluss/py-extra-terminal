
# py-extra-terminal [![py-extra-terminal](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=fff)](https://github.com/tolgakurtuluss/py-extra-terminal#readme) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/py-extra-terminal?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/py-extra-terminal) 


> <img src="https://img.informer.com/icons/png/128/1640/1640832.png" align="right"/>

`py-extra-terminal` is a comprehensive Python library for automating **Attachmate EXTRA! X-treme** terminal emulators. 

It provides a high-level, Pythonic wrapper around the `EXTRA.System` COM/OLE Automation interface.

> Disclaimer : This framework is not associated with Attachmate Corporation or Micro Focus.
> 
> Formerly developed under [py-troya-connect](https://github.com/tolgakurtuluss/py-troya-connect) [![PyPI Downloads](https://static.pepy.tech/personalized-badge/py-troya-connect?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/py-troya-connect) repository that has archived.




## Features

For a detailed list of all library features, see [FEATURES.md](FEATURES.md).

- **Easy Connection**: Simple context manager for handling COM lifecycle.
- **Session Management**: Open, close, and switch between multiple terminal sessions.
- **Screen Interaction**: Read and write text to specific coordinates, send special keys, and move the cursor.
- **Synchronization**: Built-in methods to wait for host status (quiet), specific strings, or cursor positions.
- **Modern Python**: Type hints, context managers, and exception handling.

## Installation

```bash
pip install py-extra-terminal
```

*Note: Requires Attachmate EXTRA! X-treme to be installed on Windows.*

## Basic Functions Explained

The `py-extra-terminal` library provides intuitive methods for terminal interaction. Here are the core building blocks:

### 1. Connecting and Sessions
The `Extra` class is your entry point. It manages the connection to the Attachmate EXTRA! System.

```python
from py_extra import Extra

with Extra() as ex:
    # Use the currently active window
    sess = ex.active_session
    
    # Or open a specific profile
    # sess = ex.open_session(r"C:\Path\To\Session.edp")
    
    print(f"Connected to: {sess.name}")
```

### 2. Reading Screen Content
You can read the entire screen, specific lines, or rectangular areas.

```python
sc = sess.screen

# Get full screen as a single string
full_text = sc.text()

# Read a specific field (Row 10, Col 20, Length 5)
username = sc.get(10, 20, 5)

# Find coordinates of text on screen
row, col = sc.find("LOGIN ERROR")
```

### 3. Writing and Sending Keys
Interaction is fluent and supports coordinate-based or cursor-relative writing.

```python
# Move to a field and write
sc.move(12, 40).put("MY_DATA", 12, 40)

# Send special keys from the keys module
from py_extra import keys
sc.send(keys.PF3).wait_quiet()

# Convenience: Write + Enter + Wait in one call
sc.enter("COMMAND_NAME", 24, 2)
```

### 4. Synchronization and Status
Terminal automation requires precise timing. `py-extra-terminal` handles this with built-in waiters.

```python
# Wait for host traffic to stop (Critical for reliability)
sc.wait_quiet()

# Wait for a specific message to appear
sc.wait_for("READY")

# Branching logic: Wait for one of several outcomes
result = sc.wait_for_any(["SUCCESS", "ACCESS DENIED", "SYSTEM BUSY"])

# Check if the keyboard is locked by the mainframe
if sc.is_locked:
    print("Mainframe is processing...")
```

## Quick Start Example

```python
from py_extra import Extra, keys

with Extra() as ex:
    sess = ex.active_session
    sc = sess.screen
    
    # Login scenario
    sc.wait_for("USERID")
    sc.put("MYUSER", 10, 20)
    sc.put("MYPASS", 11, 20)
    sc.enter() # Automatically sends <Enter> and waits
    
    # Check result
    if "WELCOME" in sc.text():
        print("Logged in successfully!")
```

### Scraping a List

```python
from py_extra import Extra, keys

with Extra() as ex:
    sc = ex.active_session.screen
    rows = []
    
    while True:
        # Extract data from a table
        for r in range(6, 20):
            line = sc.get(r, 2, 78)
            if line.strip():
                rows.append(line)
        
        # Check if there is more data
        if "MORE" not in sc.get(24, 60, 10):
            break
            
        # Send Page Down (PF8)
        sc.send(keys.PF8).wait_quiet()
```

## Special Keys

Special terminal keys are available in the `py_extra.keys` module:

- `keys.ENTER`
- `keys.TAB`, `keys.BACKTAB`
- `keys.PF1` through `keys.PF24`
- `keys.UP`, `keys.DOWN`, `keys.LEFT`, `keys.RIGHT`
- `keys.CLEAR`, `keys.RESET`, `keys.PA1`, etc.

## Requirements

- **Windows OS**
- **Attachmate EXTRA! X-treme**
- **Python 3.8+**
- **pywin32**

*Important: The bitness of your Python installation (32-bit vs 64-bit) must match the bitness of your EXTRA! X-treme installation for the COM automation to work correctly.*

## License

MIT
