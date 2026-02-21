[[AI article]]
feedback on main branch. which was outdated

# Architecture Overview

BQt is a Blender addon that bridges Qt/PySide2 with Blender's event loop. The core architecture uses:
- Timer-based event loop integration (15 FPS polling)
- Platform abstraction layer for Windows/macOS
- Central widget manager with registry pattern
- Window wrapping approach (Blender window becomes Qt foreign window)

---
## Strengths

✅ Clean Platform Abstraction

The blender_applications/ module hierarchy is well-designed:
- Base class defines interface
- Platform-specific implementations override only what's necessary
- Clean separation between Windows/macOS concerns

✅ Practical Problem Solving

The Windows modifier key fix (focus.py) shows deep understanding of real-world integration issues. While imperfect, it's
documented honestly with known limitations.

✅ Simple Public API

The demo code shows an excellent developer experience:
```python
  main_window = QApplication.instance().blender_widget
  dlg = MyDialog(main_window)
  dlg.show()
```
This is intuitive and follows Qt conventions.

✅ Good Documentation Structure

Wiki + demos + README provides multiple learning paths for different user types.

---
## Architectural Concerns

### ⚠️ PySide2 vs PySide6 Confusion

Critical Issue: Documentation says "PySide6" but code imports PySide2:
- README.md states "PySide6 widget support"
- `setup.py` lists PySide2 as dependency
- Code uses `from PySide2.QtWidgets import ...`

Impact: Users expecting [[PySide6]] will face import errors. This needs immediate clarification.

### ⚠️ Global State Management

widget_manager.py uses module-level list for widget tracking:
```python
  _widget_data = []  # Module-level global
```

Problems:
- Not thread-safe
- Hard to test in isolation
- Implicit state sharing
- No clear lifecycle management

Recommendation: Refactor to [[singleton]] class or instance managed by `BlenderApplication`:
```python
  class WidgetRegistry:
      def __init__(self):
          self._widgets = []
          self._lock = threading.Lock()

      def add(self, widget):
          with self._lock:
              # ... safe registration
```

### ⚠️ Polling-Based Focus Detection

15 FPS timer constantly checks window focus state:
```
  tick = int(1000 / FOCUS_FRAMERATE)  # ~66ms
  self.timer.start(tick)
```

Concerns:
- CPU overhead from continuous polling
- 66ms latency in focus detection
- Scales poorly with multiple widgets

Recommendation: Investigate event-driven alternatives:
- Windows: `WM_ACTIVATE`, `WM_SETFOCUS` messages via message hooks
- macOS: NSNotificationCenter observers for window focus changes

### ⚠️ Incomplete Error Handling

```python
  widget_manager.py silently catches all widget iteration errors:
  try:
      widget = widget_data.widget
  except RuntimeError:
      continue  # Widget deleted, no logging
```

Problems:
- Silent failures hard to debug
- No telemetry on widget lifecycle issues
- Users won't know why widgets disappear

Recommendation: Add optional debug logging:
```python
  import logging
  logger = logging.getLogger(__name__)

  try:
      widget = widget_data.widget
  except RuntimeError as e:
      logger.debug(f"Widget {widget_data} deleted: {e}")
      continue
```

### ⚠️ Unimplemented Unregistration

From `__init__.py`:
```
  def unregister():
      """Blender is wrapped in qt already. Can't unwrap it."""
      return
```

Problems:
- Addon disable doesn't clean up
- Memory leaks from lingering widgets
- QApplication persists after unregistration

Recommendation: At minimum:
- Destroy all registered widgets
- Stop the QTimer
- Clear widget registry
- Document that full cleanup requires Blender restart

---
## Code Quality & Maintenance

� Testing

Missing: No tests directory, no CI testing workflow

Impact:
- Platform-specific bugs hard to catch
- Refactoring risky
- Regression potential high

Recommendation:
1. Add pytest suite with mocked Blender environment
2. Platform-specific integration tests
3. GitHub Actions CI for each platform

� Linting Inconsistencies

- .pylintrc configured but many rules disabled
- Pre-commit has Black (120 chars) but pylint allows 150 chars
- Flake8 & Bandit commented out but not removed

Recommendation: Pick one standard and enforce it:
```yaml
# Either go all-in on Black formatting:
  repos:
    - repo: https://github.com/psf/black
      hooks:
        - id: black
          args: [--line-length=120]

# Or combine with flake8 for linting
- repo: https://github.com/pycqa/flake8
  hooks:
	- id: flake8
	  args: [--max-line-length=120]
```

� Type Hints

Missing entirely: No type annotations

Impact:
- IDE autocomplete limited
- Harder for contributors to understand interfaces
- Runtime type errors

Recommendation: Gradually add types starting with public API:
```python
  from typing import Optional
  from PySide2.QtWidgets import QWidget

  def add(widget: QWidget, show: bool = True) -> None:
      """Register a widget with the manager."""
      ...
```

---
Platform Support

� Linux Support

From `__init__.py`:
```python
  # TODO: finish implementation for linux
  else:
      return None
```

Impact: Addon silently fails on Linux

Recommendation:
1. Either implement Linux support or document it's unsupported
2. Raise clear error: raise NotImplementedError("Linux support coming soon")
3. Add Linux to CI if implementing

� Windows-Specific Issues

The stuck modifier keys bug shows deep Windows integration challenges. The current fix is acknowledged as incomplete.

Recommendation:
- Consider using Win32 hooks for proper event interception
- Add issue template for users to report keyboard state bugs
- Document known limitations in README

---
Documentation & Developer Experience

� API Documentation

Missing: No docstring standardization, no API reference

Example from `widget_manager.py`:
```python
  def add(widget, show=True):
      """TODO update the docs here"""
```

  Recommendation: Standardize on Google or NumPy docstring style:
```python
  def add(widget: QWidget, show: bool = True) -> None:
      """Register a Qt widget with the BQt manager.

      The widget will be parented to Blender's main window and tracked
      for focus/visibility management.

      Args:
          widget: The Qt widget to register
          show: Whether to immediately show the widget (default: True)

      Example:
          >>> app = QApplication.instance()
          >>> dialog = QDialog(app.blender_widget)
          >>> bqt.widget_manager.add(dialog)
      """
```

� Environment Variables

README mentions env vars but details are in wiki.

Recommendation: Add to README:
## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BQT_DISABLE_STARTUP` | `0` | Skip BQt initialization |
| `BQT_DISABLE_WRAP` | `0` | Disable window wrapping |
| `BQT_FOREGROUND` | `1` | Control widget foreground behavior |

� Version Mismatch

- bl_info says version (1, 0)
- setup.py says version 1.1.0
- Latest release is 2.0.1

Critical: These must be synchronized or users face confusion.

---
Security & Stability

� Event Interception Risk

BlenderApplication.notify() intercepts all Qt events. This is powerful but dangerous:

```
  def notify(self, receiver, event):
      # Intercepts every Qt event in the application
```

Concerns:
- Performance overhead
- Easy to introduce bugs affecting all widgets
- Hard to debug event-related issues

Recommendation:
- Add performance profiling
- Document which events are actually intercepted
- Consider more targeted event filtering

� Foreign Window Risks

Wrapping Blender's window as Qt foreign window is clever but fragile:
- OS updates can break assumptions
- Window manager differences
- Multi-monitor edge cases

Recommendation: Add defensive checks and better error messages when window wrapping fails.

---
## Specific Recommendations

Priority 1 - Critical

1. ✅ Fix PySide2/6 confusion - Update all documentation to match actual dependency
2. ✅ Synchronize version numbers - One source of truth (use __version__ in __init__.py)
3. ✅ Add error handling - Clear messages when addon fails to initialize
4. ✅ Document Linux status - Either implement or clearly mark unsupported

Priority 2 - Important

5. ✅ Add basic tests - At least smoke tests for widget registration
6. ✅ Implement cleanup - Partial unregister() better than none
7. ✅ Add type hints - Start with public API (add(), BlenderApplication interface)
8. ✅ Improve logging - Optional debug mode for troubleshooting

Priority 3 - Enhancement

9. ✅ Refactor global state - Move to managed singleton
10. ✅ Event-driven focus - Replace polling with OS events
11. ✅ Complete API docs - Standardized docstrings throughout
12. ✅ Performance profiling - Measure timer overhead, optimize hot paths

---
## Overall Assessment

**Strengths**: Solves a real problem elegantly with a clean API. Platform abstraction is well-designed. Practical approach to
integration challenges.

**Weaknesses**: Global state management, polling-based design, missing tests, documentation inconsistencies, incomplete cleanup.

**Grade: B+ -** Production-ready for its use case, but needs polish for long-term maintenance and contribution.

The project shows strong technical understanding of Qt/Blender integration, but would benefit from modern Python best practices (typing, testing, structured logging) and better lifecycle management.

[[AI feedback BQt main - cleaned up]]