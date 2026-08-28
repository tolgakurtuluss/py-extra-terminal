"""py-extra: Attachmate EXTRA! X-treme terminal automation (COM-based)."""
from __future__ import annotations

import time
import contextlib
from typing import List, Tuple, Optional, Callable, TypeVar

import win32com.client
import pythoncom

T = TypeVar("T")

class ExtraError(RuntimeError):
    """General py-extra error."""


class ScreenTimeout(ExtraError):
    """Expected screen content did not appear within the timeout period."""


def retry(fn: Callable[[], T], attempts: int = 3, delay: float = 1.0, 
          on_retry: Optional[Callable[[int, Exception], None]] = None) -> T:
    """
    Retries a function multiple times if it raises ScreenTimeout.
    Useful for handling transient host delays.
    """
    for i in range(attempts):
        try:
            return fn()
        except ScreenTimeout as exc:
            if i == attempts - 1:
                raise
            if on_retry:
                on_retry(i + 1, exc)
            time.sleep(delay)
    # Should not reach here due to raise in loop
    raise ScreenTimeout("Retry failed")


class Screen:
    """Represents the terminal screen and provides methods to interact with it."""

    def __init__(self, com_screen, default_timeout: float = 15.0):
        self._s = com_screen
        self.default_timeout = default_timeout

    # ---- OIA / Keyboard Lock Status ----
    @property
    def x_status(self) -> int:
        """
        Returns OIA XStatus (keyboard status).
        Typically, 0 indicates ready/uninhibited.
        """
        try:
            return int(self._s.OIA.XStatus)
        except Exception:
            return 0

    @property
    def updating(self) -> bool:
        """Returns True if the screen is currently updating or receiving host traffic."""
        try:
            return bool(self._s.OIA.Updating)
        except Exception:
            return False

    @property
    def is_locked(self) -> bool:
        """
        Checks if the keyboard is locked or inhibited.
        Returns True if updating is active or keyboard state (XStatus) is locked/inhibited (not 0).
        """
        return self.updating or (self.x_status != 0)

    # ---- Reading ----
    @property
    def rows(self) -> int:
        """Returns the number of rows in the screen."""
        return int(self._s.Rows)

    @property
    def cols(self) -> int:
        """Returns the number of columns in the screen."""
        return int(self._s.Cols)

    @property
    def cursor(self) -> Tuple[int, int]:
        """Returns the current cursor position as (row, col)."""
        return int(self._s.Row), int(self._s.Col)

    def get(self, row: int, col: int, length: int) -> str:
        """Reads a string from the screen at the specified position."""
        # Use 1-based indexing for row and col as per EXTRA! specs
        r = int(row)
        c = int(col)
        l = int(length)
        
        try:
            # Attempt direct method call
            val = self._s.GetString(r, c, l)
            return str(val)
        except Exception:
            try:
                # Use Area if GetString is problematic
                area = self._s.Area(r, c, r, c + l - 1)
                return str(area.Value)
            except Exception:
                return ""

    def get_at_cursor(self, length: int) -> str:
        """Reads a string starting from the current cursor position."""
        r, c = self.cursor
        return self.get(r, c, length)

    def area(self, r1: int, c1: int, r2: int, c2: int) -> str:
        """Returns the text within the specified rectangular area."""
        return str(self._s.Area(r1, c1, r2, c2).Value)

    def dump(self) -> List[str]:
        """Returns the entire screen as a list of strings (one per row)."""
        rows = self.rows
        cols = self.cols
        return [self.get(r, 1, cols) for r in range(1, rows + 1)]

    def text(self) -> str:
        """Returns the entire screen as a single string with newlines."""
        return "\n".join(self.dump())

    def find(self, needle: str) -> Optional[Tuple[int, int]]:
        """
        Searches the entire screen for the specified string (needle).
        Returns the (row, col) coordinate of the first occurrence, or None if not found.
        """
        rows = self.rows
        cols = self.cols
        for r in range(1, rows + 1):
            row_text = self.get(r, 1, cols)
            idx = row_text.find(needle)
            if idx != -1:
                return r, idx + 1
        return None

    # ---- Writing ----
    def put(self, text: str, row: int, col: int) -> Screen:
        """Writes text to the screen at the specified position."""
        func = self._s.PutString
        if callable(func):
            func(text, row, col)
        else:
            # If it's a property (unlikely for PutString but for consistency)
            self._s.PutString = text
        return self

    def put_at_cursor(self, text: str) -> Screen:
        """Writes text to the screen at the current cursor position."""
        r, c = self.cursor
        return self.put(text, r, c)

    def clear_area(self, r1: int, c1: int, r2: int, c2: int) -> Screen:
        """Clears the specified rectangular area of the screen with spaces."""
        for r in range(r1, r2 + 1):
            width = c2 - c1 + 1
            if width > 0:
                self.put(" " * width, r, c1)
        return self

    def clear_line(self, row: int) -> Screen:
        """Clears the entire row with spaces."""
        return self.put(" " * self.cols, row, 1)

    def send(self, keys: str) -> Screen:
        """Sends keys (including special control keys) to the screen."""
        func = self._s.SendKeys
        if callable(func):
            func(keys)
        else:
            self._s.SendKeys = keys
        return self

    def move(self, row: int, col: int) -> Screen:
        """Moves the cursor to the specified position."""
        func = self._s.MoveTo
        if callable(func):
            func(row, col)
        else:
            self._s.MoveTo = (row, col)
        return self

    def enter(self, text: Optional[str] = None, row: Optional[int] = None, col: Optional[int] = None) -> Screen:
        """Writes text (optional), sends <Enter>, and waits for the host to be quiet."""
        if text is not None:
            if row is not None and col is not None:
                self.put(text, row, col)
            else:
                self.send(text)
        self.send("<Enter>")
        return self.wait_quiet()

    # ---- Waiting ----
    def wait_quiet(self, ms: int = 1000, timeout: Optional[float] = None) -> Screen:
        """Waits until the host traffic stops (OIA.Updating is False)."""
        tmo = int((timeout or self.default_timeout) * 1000)
        
        try:
            # WaitHostQuiet signature might vary by EXTRA! version.
            # In some versions it takes ms, in others it might be a property or no-arg.
            if ms:
                self._s.WaitHostQuiet(int(ms))
        except Exception:
            try:
                self._s.WaitHostQuiet()
            except Exception:
                pass
        
        deadline = time.time() + (tmo / 1000)
        # Check OIA.Updating to ensure host is not processing
        while self.updating:
            if time.time() > deadline:
                raise ScreenTimeout("Host remained busy (OIA.Updating)")
            time.sleep(0.05)
        return self

    def wait_for(self, needle: str, row: Optional[int] = None,
                 col: Optional[int] = None, timeout: Optional[float] = None) -> Screen:
        """Waits until the specified text appears on the screen."""
        deadline = time.time() + (timeout or self.default_timeout)
        while time.time() < deadline:
            hay = self.get(row, col, len(needle)) if row else self.text()
            if needle in hay:
                return self
            time.sleep(0.2)
        raise ScreenTimeout(f"{needle!r} not found within {timeout or self.default_timeout}s")

    def wait_for_any(self, needles: List[str], row: Optional[int] = None,
                     col: Optional[int] = None, timeout: Optional[float] = None) -> str:
        """
        Waits until any of the specified texts (needles) appears on the screen.
        Returns the needle that appeared first.
        """
        deadline = time.time() + (timeout or self.default_timeout)
        while time.time() < deadline:
            screen_text_to_check = ""
            if row is not None and col is not None:
                # If row and col are specified, get a specific area to check
                # This assumes a length appropriate for any needle, or a wider area
                # For simplicity, if col is specified, we get the whole row
                screen_text_to_check = self.get(row, 1, self.cols) # Read entire row
            else:
                # If no row/col, get the entire screen text
                screen_text_to_check = self.text()

            for needle in needles:
                if needle in screen_text_to_check:
                    return needle
            time.sleep(0.2)
        raise ScreenTimeout(f"None of {needles!r} found within {timeout or self.default_timeout}s")

    def wait_for_change(self, timeout: Optional[float] = None) -> Screen:
        """Waits until the screen text contents change from their current state."""
        initial_text = self.text()
        deadline = time.time() + (timeout or self.default_timeout)
        while time.time() < deadline:
            if self.text() != initial_text:
                return self
            time.sleep(0.1)
        raise ScreenTimeout(f"Screen content did not change within {timeout or self.default_timeout}s")

    def wait_for_cursor(self, row: int, col: int, timeout: Optional[float] = None) -> Screen:
        """Waits until the cursor moves to the specified position."""
        deadline = time.time() + (timeout or self.default_timeout)
        while self.cursor != (row, col):
            if time.time() > deadline:
                raise ScreenTimeout(f"Cursor did not move to ({row},{col}): {self.cursor}")
            time.sleep(0.1)
        return self


class Session:
    """Represents an EXTRA! session."""

    def __init__(self, com_session, default_timeout: float = 15.0):
        self._sess = com_session
        self.screen = Screen(com_session.Screen, default_timeout)

    @property
    def name(self) -> str:
        """Returns the session name."""
        return str(self._sess.Name)

    @property
    def connected(self) -> bool:
        """Returns True if the session is connected."""
        with contextlib.suppress(Exception):
            return bool(self._sess.Connected)
        return True

    @property
    def visible(self) -> bool:
        """Returns True if the session window is visible."""
        return bool(self._sess.Visible)

    @visible.setter
    def visible(self, value: bool):
        self._sess.Visible = value

    def close(self):
        """Closes the session."""
        self._sess.Close()

    def __repr__(self):
        return f"<Session {self.name!r} connected={self.connected}>"


class Extra:
    """
    Main interface for Attachmate EXTRA! X-treme.

    Usage:
    >>> with Extra() as ex:
    ...     sess = ex.active_session
    ...     sess.screen.wait_for("LOGON", row=1, col=2)
    """

    PROGID = "EXTRA.System"

    def __init__(self, progid: Optional[str] = None, default_timeout: float = 15.0,
                 visible: bool = True):
        pythoncom.CoInitialize()
        try:
            self._sys = win32com.client.Dispatch(progid or self.PROGID)
        except pythoncom.com_error as exc:
            raise ExtraError(
                "EXTRA! X-treme COM server not found. Is it installed? "
                "Ensure Python and EXTRA! have the same architecture (32/64 bit)."
            ) from exc
        self.default_timeout = default_timeout
        with contextlib.suppress(Exception):
            self._sys.Visible = visible

    @property
    def version(self) -> str:
        """Returns the EXTRA! X-treme version."""
        return str(self._sys.Version)

    @property
    def sessions(self) -> List[Session]:
        """Returns a list of all open sessions."""
        col = self._sys.Sessions
        count = int(col.Count)
        results = []
        # COM collections are often 1-indexed, but Item() can be tricky.
        # Let's try iterating directly or using indexed access.
        for i in range(1, count + 1):
            try:
                # Some COM objects prefer Item(i) others Item i
                s = col.Item(i)
                results.append(Session(s, self.default_timeout))
            except Exception:
                # Fallback for some COM implementations
                try:
                    s = col(i)
                    results.append(Session(s, self.default_timeout))
                except Exception:
                    continue
        return results

    @property
    def active_session(self) -> Session:
        """Returns the currently active session."""
        s = self._sys.ActiveSession
        if s is None:
            raise ExtraError("No active session found. Use open_session(edp_path) first.")
        return Session(s, self.default_timeout)

    def open_session(self, edp_path: str) -> Session:
        """Opens an .edp session profile and returns a Session object."""
        self._sys.Sessions.Open(edp_path)
        return self.active_session

    def session_by_name(self, name: str) -> Session:
        """Finds an open session by its name."""
        for s in self.sessions:
            if s.name.lower() == name.lower():
                return s
        raise ExtraError(f"Session {name!r} not found.")

    def close(self):
        """Uninitializes the COM interface."""
        pythoncom.CoUninitialize()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False
