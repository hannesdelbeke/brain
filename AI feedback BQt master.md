feedback on latest/live version [[claude sonnet 4.5]]

---
title: BQt Architectural Review
tags:
  - architecture
  - blender
  - qt
  - review
  - python
date: 2026-02-21
repository: https://github.com/techartorg/bqt
branch: master
version: 1.4.2
grade: A-

---

# BQt Architectural Review

> [!info] Repository Details
> - **URL**: https://github.com/techartorg/bqt
> - **Branch**: master
> - **Version**: 1.4.2 (transitioning to 2.0.0)
> - **Stars**: 198
> - **License**: MPL-2.0
> - **Languages**: 100% Python

---

## Executive Summary

> [!success] Overall Assessment
> **BQt** is a production-ready Blender addon that integrates PySide6/Qt into Blender's event loop, enabling developers to create fully custom UIs beyond Blender's N-Panel limitations. The architecture is well-designed with clean platform abstraction, though some areas could benefit from modernization and improved error handling.
>
> **Grade**: **A-**

---

## Architecture Overview

### Core Design Patterns

**Event Loop Integration**
- Timer-based polling (15 FPS) to monitor window focus changes
- QApplication wraps Blender's window as a Qt foreign window
- Persistent handlers hook into Blender's event system

**Platform Abstraction**
```
BlenderApplication (ABC)
├── DarwinBlenderApplication (macOS)
└── Win32BlenderApplication (Windows)
```

**Widget Management**
- Central registry pattern via `bqt.manager`
- Automatic widget discovery and parenting
- Configurable via environment variables

### Key Components

| Module | Responsibility |
|--------|---------------|
| `__init__.py` | Addon registration, QApplication lifecycle |
| `manager.py` | Widget registry, auto-parenting, visibility management |
| `blender_applications/` | Platform-specific window handling |
| `focus.py` | Windows keyboard bug workarounds |
| `utils.py` | Decorators for error handling and context management |

---

## Strengths

### ✅ Clean Platform Abstraction

> [!check] Exemplary Design
> The platform-specific implementations demonstrate excellent separation of concerns and make future platform additions (Linux) straightforward.

```python
# Base class defines interface
class BlenderApplication(QApplication):
    @abstractstaticmethod
    def _get_blender_hwnd() -> int:
        """Get the handler window ID for the blender application window"""

# Windows implements with ctypes
class Win32BlenderApplication(BlenderApplication):
    @staticmethod
    def _get_blender_hwnd() -> int:
        hwnd = get_blender_window()
        return hwnd
```

**Impact**: Easy to add Linux support or maintain platform-specific code independently.

### ✅ Environment Variable Configuration

> [!tip] Power User Features
> Excellent use of env vars for feature flags without requiring code changes.

| Variable | Default | Purpose |
|----------|---------|---------|
| `BQT_DISABLE_STARTUP` | `0` | Skip initialization |
| `BQT_DISABLE_WRAP` | `0` | Disable window wrapping |
| `BQT_MANAGE_FOREGROUND` | `1` | Widget foreground management |
| `BQT_AUTO_ADD` | `1` | Auto-parent orphan widgets |
| `BQT_DOCKABLE_WRAP` | `1` | Wrap widgets in QDockWidget |
| `BQT_UNIQUE_OBJECTNAME` | `1` | Prevent duplicate widgets |
| `BQT_LOG_LEVEL` | `WARNING` | Logging verbosity |
| `BQT_DISABLE_CLOSE_DIALOGUE` | `0` | Skip custom close dialog |

### ✅ Excellent Developer Experience

> [!example] Simple API
> No manual registration needed - widgets are auto-discovered!

```python
from PySide6.QtWidgets import QApplication, QDialog

# Get Blender's main window
main_window = QApplication.instance().blender_widget

# Create and show your widget
dlg = QDialog(main_window)
dlg.show()  # BQt automatically registers it
```

### ✅ Practical Utility Functions

```python
@bqt.utils.try_except
def my_function():
    # Won't crash Blender on exception
    risky_operation()

@bqt.utils.context_window
def run_operator():
    # Ensures valid Blender context for operators
    bpy.ops.mesh.primitive_cube_add()
```

### ✅ Proper Logging

Structured logging throughout with configurable levels:

```python
logger = logging.getLogger("bqt")
logger.debug(f"registering widget with bqt '{widget}'")
```

### ✅ Window State Persistence

Geometry, maximized state, and fullscreen mode are preserved across sessions via `QSettings`.

### ✅ Smart Window Title Management

> [!note] Blender Integration
> Integrates seamlessly with Blender's save system to show file state in window title.

```python
def _title(check_dirty=True):
    title = f"{WINDOW_TITLE} {bpy.app.version_string}"
    if not bpy.data.is_saved:
        title = f"(Unsaved) - {title}"
    else:
        f = Path(bpy.data.filepath)
        title = f"{f.stem} [{f.as_posix()}] - {title}"
    if check_dirty and bpy.data.is_dirty:
        title = f"* {title}"  # Dirty indicator
    return title
```

---

## Architectural Concerns

### ⚠️ Global State in Widget Manager

> [!warning] Thread Safety Issue
> Module-level lists for widget tracking are not thread-safe and hard to test in isolation.

**Current Issue**:
```python
# manager.py
__widgets = []  # Module-level global
__excluded_widgets = []
```

**Problems**:
- Not thread-safe (Qt can be multi-threaded)
- Hard to test in isolation
- No clear ownership or lifecycle
- Implicit coupling

> [!example] Recommended Solution
> Refactor to singleton or instance-managed registry

```python
class WidgetRegistry:
    """Thread-safe widget registry with clear lifecycle"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._widgets = []
            cls._instance._excluded = []
            cls._instance._lock = threading.Lock()
        return cls._instance

    def register(self, widget, **kwargs):
        with self._lock:
            # ... safe registration

# Usage
registry = WidgetRegistry()
registry.register(my_widget)
```

### ⚠️ Polling-Based Focus Detection

> [!warning] Performance Concern
> 15 FPS timer constantly polls window state, causing continuous CPU usage even when idle.

**Current Issue**:
```python
tick = int(1000 / FOCUS_FRAMERATE)  # ~66ms
self.timer.start(tick)

def on_update(self):
    # Runs every 66ms
    if self.blender_focus_toggled():
        bqt.manager._blender_window_change(self._active_window_hwnd)
```

**Problems**:
- Continuous CPU usage even when idle
- 66ms latency in focus detection
- Doesn't scale well with many widgets
- Battery drain on laptops

> [!tip] Event-Driven Alternative
> Use OS-native event hooks instead of polling

**Windows**:
```python
# Use Win32 message hooks for WM_ACTIVATE
def install_focus_hook():
    WH_CALLWNDPROC = 4
    callback = WINFUNCTYPE(c_long, c_int, c_uint, c_long)

    def hook_proc(nCode, wParam, lParam):
        if msg.message == WM_ACTIVATE:
            on_focus_changed(wParam != WA_INACTIVE)
        return CallNextHookEx(None, nCode, wParam, lParam)

    hook = callback(hook_proc)
    SetWindowsHookEx(WH_CALLWNDPROC, hook, None, GetCurrentThreadId())
```

**macOS**:
```python
# Use NSNotificationCenter
from AppKit import NSWorkspace, NSNotificationCenter

def setup_focus_observer():
    nc = NSNotificationCenter.defaultCenter()
    nc.addObserver_selector_name_object_(
        self,
        'applicationDidBecomeActive:',
        'NSApplicationDidBecomeActiveNotification',
        None
    )
```

**Impact**: Could reduce idle CPU usage to near-zero.

### ⚠️ Incomplete Error Handling

> [!bug] Silent Failures
> Widget cleanup happens silently without logging, making debugging difficult.

```python
def iter_widget_data():
    cleanup = []
    for widget_data in __widgets:
        try:
            v = widget_data.widget.isVisible()
        except RuntimeError:
            cleanup.append(widget_data)
            continue  # Silent failure
```

**Problems**:
- No logging of why widgets were removed
- Hard to debug disappearing widgets
- No telemetry on lifecycle issues

> [!example] Add Contextual Logging
```python
def iter_widget_data():
    cleanup = []
    for widget_data in __widgets:
        try:
            v = widget_data.widget.isVisible()
        except RuntimeError as e:
            logger.debug(
                f"Widget {widget_data.widget.objectName() or 'unnamed'} "
                f"was deleted: {e}"
            )
            cleanup.append(widget_data)
            continue
```

### ⚠️ Linux Support Missing

> [!error] Platform Gap
> Linux users are completely excluded with a `NotImplementedError`.

```python
elif operating_system in ["linux", "linux2"]:
    raise NotImplementedError("Linux is not supported yet")
```

**Impact**: Growing Blender Linux user base is excluded

> [!todo] Recommended Actions
> 1. **Implement Linux support** using X11/Wayland APIs
> 2. **Provide graceful degradation** (basic Qt without wrapping)
> 3. **Document clearly** in README which features work on Linux

**Example Linux implementation approach**:
```python
# For X11
import ctypes
x11 = ctypes.CDLL("libX11.so.6")
x11.XOpenDisplay.restype = ctypes.c_void_p

def get_blender_window_x11():
    display = x11.XOpenDisplay(None)
    root = x11.XDefaultRootWindow(display)
    # ... enumerate windows
```

### ⚠️ Windows Keyboard Bug Workaround is Fragile

> [!bug] Known Issue
> The keyboard stuck-key fix is acknowledged as imperfect and can affect first keypress after refocus.

From `focus.py`:
```python
def _detect_keyboard(hwnd=None):
    """force a release of 'stuck' keys"""
    # Commented note: "this bug fix is not perfect yet"
    for name, code in keycodes:
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)
```

**Problems**:
- Acknowledged as imperfect
- Simulates key releases globally (could affect other apps)
- First keypress sometimes ignored after refocus
- Input occasionally freezes requiring mouse click

> [!todo] Recommended Actions
> 1. **Deep dive into root cause** - Why are keys stuck?
> 2. **Consider keyboard hooks** instead of simulation
> 3. **Add issue template** for users to report keyboard bugs
> 4. **Document known limitations** in README

### ⚠️ Unimplemented `unregister()`

> [!warning] Memory Leaks
> Addon disable doesn't clean up, causing memory leaks and lingering Qt state.

**Current Issue**:
```python
def unregister():
    """Runs on disabling the add-on."""
    logger.debug("unregistering bqt add-on")
    logger.warning("unregistering bqt is not supported yet, skipping")
    # ... rest commented out
```

**Problems**:
- Memory leaks from lingering widgets
- QApplication persists after addon disable
- Handlers remain registered
- Can't properly disable addon without restarting Blender

> [!example] Implement Partial Cleanup
```python
def unregister():
    logger.debug("unregistering bqt add-on")

    try:
        # Stop the timer
        app = QApplication.instance()
        if app and hasattr(app, 'timer'):
            app.timer.stop()

        # Destroy all registered widgets
        import bqt.manager
        for widget_data in list(bqt.manager.__widgets):
            widget_data.widget.deleteLater()
        bqt.manager.__widgets.clear()

        # Remove Blender handlers
        if app:
            handlers_to_remove = [
                app.update_window_title,
                app.update_window_title_post_save
            ]
            for handler in handlers_to_remove:
                if handler in bpy.app.handlers.depsgraph_update_post:
                    bpy.app.handlers.depsgraph_update_post.remove(handler)
                # ... similar for other handler lists

        logger.info("BQt unregistered (restart Blender for full cleanup)")

    except Exception as e:
        logger.error(f"Error during unregister: {e}")
```

> [!note] Documentation Addition
> Add to README: "Disabling BQt requires restarting Blender for complete cleanup due to QApplication lifecycle limitations."

### ⚠️ Duplicate Widget Detection Could Be Smarter

> [!bug] Incomplete Duplicate Detection
> Only checks `objectName`, allowing widgets without names to duplicate.

**Current Issue**:
```python
if unique and os.getenv("BQT_UNIQUE_OBJECTNAME", "1") == "1":
    obj_name = widget.objectName()
    if obj_name:  # Empty names bypass check
        for data in iter_widget_data():
            if data.widget.objectName() == obj_name:
                old_widget = data.widget
                break
```

**Problems**:
- Widgets without `objectName` can duplicate
- No way to detect same widget type without name
- Deletes new widget which might be intentional

> [!example] Smarter Detection
```python
def is_duplicate_widget(widget, check_type=True):
    """Check if widget is a duplicate based on name and optionally type"""
    obj_name = widget.objectName()
    widget_type = type(widget).__name__

    for data in iter_widget_data():
        existing = data.widget
        name_match = obj_name and (existing.objectName() == obj_name)
        type_match = check_type and (type(existing).__name__ == widget_type)

        if name_match or (not obj_name and type_match):
            logger.debug(
                f"Found potential duplicate: {widget_type} "
                f"(name: '{obj_name or 'unnamed'}')"
            )
            return existing
    return None
```

---

## Code Quality

### � Testing - Missing

> [!error] Critical Gap
> No test suite found - platform-specific bugs hard to catch before release.

**Impact**:
- Platform-specific bugs hard to catch before release
- Refactoring is risky
- Contributors can't verify changes

> [!example] Recommended Test Suite
```python
# tests/test_manager.py
import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QWidget
import bqt.manager

@pytest.fixture
def mock_qapp():
    app = Mock()
    app.blender_widget = Mock()
    with patch('PySide6.QtWidgets.QApplication.instance', return_value=app):
        yield app

def test_register_widget(mock_qapp):
    widget = Mock(spec=QWidget)
    widget.isVisible.return_value = True
    widget.objectName.return_value = "test_widget"

    bqt.manager.register(widget)

    # Verify widget was added
    assert len(bqt.manager.__widgets) > 0

def test_duplicate_prevention(mock_qapp):
    widget1 = Mock(spec=QWidget)
    widget1.objectName.return_value = "duplicate"
    widget2 = Mock(spec=QWidget)
    widget2.objectName.return_value = "duplicate"

    bqt.manager.register(widget1)
    bqt.manager.register(widget2)

    # widget2 should be deleted
    widget2.deleteLater.assert_called_once()
```

**Add to `pyproject.toml`**:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-qt",
    "pytest-mock",
]
```

### � Type Hints - Partial

> [!warning] Inconsistent Type Safety
> Some functions have type hints, others don't.

**Current State**:
```python
# Has hints
def _instantiate_q_application() -> "bqt.blender_applications.BlenderApplication":
    ...

# Missing hints
def register(widget, exclude=None, parent=True, manage=True, unique=True):
    ...
```

> [!example] Add Type Hints to Public API
```python
from typing import Optional, List
from PySide6.QtWidgets import QWidget

def register(
    widget: QWidget,
    exclude: Optional[List[QWidget]] = None,
    parent: bool = True,
    manage: bool = True,
    unique: bool = True
) -> None:
    """
    Register a Qt widget with BQt's management system.

    Args:
        widget: The Qt widget to register
        exclude: Widgets to exclude from parenting
        parent: Whether to parent widget to Blender window
        manage: Whether to manage visibility automatically
        unique: Prevent duplicate widgets with same objectName
    """
    ...
```

**Add to `pyproject.toml`**:
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Gradual typing
```

### � Linting - Configured but Permissive

**Current**:
- ✅ Black with 120 char line length
- ❌ Flake8 commented out
- ❌ Bandit (security) commented out

> [!tip] Enable Full Linting
```yaml
# .pre-commit-config.yaml
- repo: https://github.com/pycqa/flake8
  rev: 6.0.0
  hooks:
    - id: flake8
      args: [
        "--max-line-length=120",
        "--extend-ignore=E203,W503",  # Black compatibility
        "--exclude=*test*,__pycache__"
      ]

- repo: https://github.com/PyCQA/bandit
  rev: 1.7.5
  hooks:
    - id: bandit
      args: ["-c", "pyproject.toml"]
      additional_dependencies: ["bandit[toml]"]
```

**Add security config**:
```toml
# pyproject.toml
[tool.bandit]
exclude_dirs = ["tests"]
skips = ["B101"]  # assert_used (OK in Blender context)
```

---

## Security & Stability

### � Global Event Interception

> [!warning] Performance Risk
> `notify()` intercepts **every** Qt event in the application.

```python
def notify(self, receiver: QObject, event: QEvent) -> bool:
    # Handles ALL events in the entire Qt application
    if isinstance(event, QCloseEvent) and receiver in (self.blender_widget, self._blender_window):
        # ... handle close
```

**Concerns**:
- Performance overhead on every mouse move, key press, paint event
- Easy to introduce bugs affecting all widgets
- Hard to debug event-related issues

> [!tip] Use Event Filters Instead
```python
class CloseEventFilter(QObject):
    def eventFilter(self, obj, event):
        if isinstance(event, QCloseEvent):
            event.ignore()
            self.handle_close()
            return True
        return False

# Install only on specific widgets
filter = CloseEventFilter()
self.blender_widget.installEventFilter(filter)
```

### � Foreign Window Wrapping Fragility

> [!warning] OS-Dependent Behavior
> Wrapping Blender's native window as Qt foreign window works but is fragile across OS updates and configurations.

**Risks**:
- OS updates can break assumptions
- Window manager differences (GNOME vs KDE vs Windows DWM)
- Multi-monitor edge cases
- Wayland vs X11 on Linux
- Different behavior on Apple Silicon vs Intel

> [!example] Add Defensive Checks
```python
def _wrap_blender_window(self):
    """Wrap Blender's window in Qt with extensive validation"""
    try:
        hwnd = self._get_blender_hwnd()
        if not hwnd:
            raise ValueError("Could not obtain Blender window handle")

        # Validate window is actually visible and valid
        if not self._validate_window_handle(hwnd):
            raise ValueError(f"Window handle {hwnd} is invalid")

        self._blender_window = QWindow.fromWinId(hwnd)

        # Verify wrapping succeeded
        if not self._blender_window.isVisible():
            logger.warning("Wrapped window is not visible")

        return True

    except Exception as e:
        logger.error(f"Failed to wrap Blender window: {e}")
        logger.info("Falling back to non-wrapped mode")
        os.environ["BQT_DISABLE_WRAP"] = "1"
        return False
```

### � ctypes Usage

> [!caution] Memory Safety
> Heavy use of `ctypes` for Windows/macOS APIs requires careful validation.

```python
# Direct Win32 calls
ctypes.windll.user32.SetFocus(self._hwnd)
ctypes.windll.user32.keybd_event(code, 0, 2, 0)
```

**Risks**:
- Incorrect argument types can crash Python
- No type safety
- OS version differences

> [!check] Code Appears Production-Tested
> Current implementation seems well-tested in production.

> [!example] Add Validation Layer
```python
def safe_win32_call(func, *args, check_zero=False):
    """Safely call Win32 API with error checking"""
    try:
        result = func(*args)
        if check_zero and result == 0:
            error = ctypes.get_last_error()
            raise ctypes.WinError(error)
        return result
    except Exception as e:
        logger.error(f"Win32 call failed: {func.__name__}({args}): {e}")
        return None

# Usage
safe_win32_call(user32.SetFocus, hwnd, check_zero=True)
```

---

## Performance Optimizations

### ⚡ Widget Iteration Optimization

> [!tip] Reduce Complexity from O(n²) to O(n)

**Current**:
```python
def iter_widget_data():
    cleanup = []
    for widget_data in __widgets:
        try:
            v = widget_data.widget.isVisible()
        except RuntimeError:
            cleanup.append(widget_data)
            continue
        yield widget_data
    for widget_data in cleanup:
        __widgets.remove(widget_data)  # O(n) per remove
```

**Optimized**:
```python
def iter_widget_data():
    """Iterate over widgets, cleaning up deleted ones efficiently"""
    global __widgets
    valid_widgets = []

    for widget_data in __widgets:
        try:
            widget_data.widget.isVisible()  # Trigger potential RuntimeError
            valid_widgets.append(widget_data)
            yield widget_data
        except RuntimeError:
            logger.debug(f"Cleaning up deleted widget")
            # Widget deleted, don't add to valid_widgets

    # Single assignment instead of multiple removes
    __widgets = valid_widgets
```

### ⚡ Orphan Widget Detection

> [!tip] Use Sets for O(1) Lookup

**Current**:
```python
def _orphan_toplevel_widgets():
    return [widget for widget in QApplication.instance().topLevelWidgets() if
            not widget.parent()
            and widget not in __widgets  # O(n) check
            and widget not in __excluded_widgets]  # O(n) check
```

**Optimized**:
```python
# Convert lists to sets for O(1) lookup
__widget_set = set()  # Maintain alongside __widgets list
__excluded_set = set()

def _orphan_toplevel_widgets():
    return [
        widget for widget in QApplication.instance().topLevelWidgets()
        if not widget.parent()
        and widget not in __widget_set  # O(1)
        and widget not in __excluded_set  # O(1)
    ]
```

### ⚡ Cache Environment Variables

> [!tip] Avoid Repeated String Lookups

**Current**:
```python
def on_update(self):
    """Runs every 66ms regardless of activity"""
    if os.getenv("BQT_DISABLE_WRAP") == "1" and ...:
        bqt.manager._blender_window_change(...)
    if os.getenv("BQT_AUTO_ADD", "1") == "1":
        bqt.manager.parent_orphan_widgets(...)
```

**Optimized**:
```python
def __init__(self):
    # Cache env var checks at startup
    self._manage_foreground = (
        os.getenv("BQT_DISABLE_WRAP") == "1" and
        os.getenv("BQT_MANAGE_FOREGROUND", "1") == "1"
    )
    self._auto_add = os.getenv("BQT_AUTO_ADD", "1") == "1"

def on_update(self):
    if self._manage_foreground and self.blender_focus_toggled():
        bqt.manager._blender_window_change(self._active_window_hwnd)

    if self._auto_add:
        bqt.manager.parent_orphan_widgets(...)
```

---

## Action Plan

### Priority 1 - Critical

> [!todo] Week 1: Foundation
> - [ ] Add basic pytest suite (widget registration, platform detection)
> - [ ] Implement partial `unregister()` cleanup
> - [ ] Add type hints to `manager.register()`
> - [ ] Enable flake8 in pre-commit

### Priority 2 - Important

> [!todo] Week 2: Stability
> - [ ] Event-driven focus (replace polling)
> - [ ] Improve error logging (add context to silent failures)
> - [ ] Type hints on public API
> - [ ] Performance profiling of `notify()` and timer

### Priority 3 - Enhancement

> [!todo] Week 3-4: Long-term
> - [ ] Refactor global state to singleton
> - [ ] Complete API docs with standardized docstrings
> - [ ] Enable flake8 & bandit
> - [ ] Optimize widget iteration and orphan detection

### Long-term Initiatives

> [!todo] Future Releases
> - [ ] Linux support feasibility study
> - [ ] Plugin architecture exploration
> - [ ] Event bus for better decoupling
> - [ ] Configuration system (YAML/TOML)

---

## Comparison to Alternatives

### vs. Blender's Built-in UI

| Feature | Blender UI | BQt |
|---------|-----------|-----|
| Learning curve | Low | Medium (Qt knowledge required) |
| Customization | Limited (N-Panel) | Unlimited (full Qt) |
| Cross-DCC | Blender only | Portable to Maya, Max, etc. |
| Widgets | Limited | Thousands available |
| Performance | Native | Slight overhead |

### vs. Manual Qt Integration

| Aspect | Manual Integration | BQt |
|--------|-------------------|-----|
| Setup complexity | High | Low (install addon) |
| Window management | Manual | Automatic |
| Blender integration | Custom hooks | Built-in |
| Maintenance | DIY | Community supported |

> [!success] Verdict
> BQt significantly lowers the barrier to entry for Qt in Blender while maintaining flexibility.

---

## Best Practices to Adopt

### Use `__all__` to Define Public API

```python
# __init__.py
__all__ = ['add', 'register']  # Clear public API

# Explicit exports
add = bqt.manager.register  # Alias for convenience
```

### Add Version Management

```python
# __init__.py
__version__ = "1.4.2"

# Update bl_info to use it
bl_info = {
    "name": "BQt - Qt for Blender",
    "version": tuple(map(int, __version__.split('.'))),
    ...
}
```

### Context Managers for State Changes

```python
from contextlib import contextmanager

@contextmanager
def widget_batch_register():
    """Temporarily disable auto-add for batch operations"""
    old_value = os.environ.get("BQT_AUTO_ADD", "1")
    os.environ["BQT_AUTO_ADD"] = "0"
    try:
        yield
    finally:
        os.environ["BQT_AUTO_ADD"] = old_value

# Usage
with widget_batch_register():
    for _ in range(100):
        create_widget()  # Won't trigger auto-add each time
```

---

## Documentation Improvements

### README Additions

> [!example] Add Troubleshooting Section
> ```markdown
> ## Troubleshooting
>
> ### Widgets disappear when switching windows
> Set `BQT_MANAGE_FOREGROUND=0` to disable automatic hiding.
>
> ### Keyboard input freezes on Windows
> Known issue when alt-tabbing. Click in Blender to resume.
> Set `BQT_DISABLE_WRAP=1` if problem persists.
>
> ### Addon won't disable
> Restart Blender for complete cleanup (limitation of Qt lifecycle).
>
> ### Linux support?
> Linux is not yet supported. Help wanted! See #123.
> ```

### API Reference

> [!example] Document Public Functions
> ```markdown
> ## API Reference
>
> ### Core Functions
>
> #### `bqt.add(widget, **kwargs)`
> Register a widget with BQt's management system.
>
> **Parameters:**
> - `widget` (QWidget): The widget to register
> - `parent` (bool, default=True): Parent to Blender window
> - `manage` (bool, default=True): Automatic visibility management
> - `unique` (bool, default=True): Prevent duplicates
>
> **Example:**
> ```python
> from PySide6.QtWidgets import QDialog, QApplication
>
> dialog = QDialog()
> dialog.setWindowTitle("My Tool")
> dialog.show()  # BQt automatically registers it
> ```
> ```

---

## Final Assessment

### What BQt Does Exceptionally Well

> [!success] Strengths
> 1. **Solves a real problem** - Enables custom UI in Blender
> 2. **Production-proven** - Used in real studios and pipelines
> 3. **Clean architecture** - Platform abstraction is exemplary
> 4. **Great DX** - Simple API, automatic widget management
> 5. **Well-documented** - README + Wiki + demos
> 6. **Active maintenance** - Responsive to issues

### Areas for Growth

> [!warning] Improvement Areas
> 1. **Testing infrastructure** - No automated tests
> 2. **Linux support** - Large user base excluded
> 3. **Performance optimization** - Polling could be event-driven
> 4. **Type safety** - Inconsistent type hints
> 5. **Lifecycle management** - Incomplete unregistration

### Final Grade: **A-**

> [!quote] Reasoning
> - **A** for architecture, API design, documentation, and production readiness
> - **Minus** for missing tests, incomplete cleanup, and platform gaps
>
> BQt is a **well-crafted, production-ready tool** that demonstrates strong software engineering principles. The platform abstraction is textbook-quality, the API is intuitive, and it solves a genuine pain point for Blender developers.
>
> The recommended improvements are largely "nice-to-haves" for long-term maintenance and scalability, not critical flaws.
>
> **For a specialized tool in the technical art domain, this is excellent work.**

---

## Related Resources

- [[Qt Integration Patterns]]
- [[Blender Python API]]
- [[Cross-DCC Tool Development]]
- [[Event Loop Architecture]]

---

#review-completed #architecture-analysis #blender-addons #qt-integration
