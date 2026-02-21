feedback on main branch. which was outdated

# BQt Architectural Analysis

**Tags:** #blender #python #pyside #architecture
**Related:** [[AI article]], [[BQt]]

## Overview

BQt is a Blender addon that bridges Qt/PySide2 with Blender's event loop. The core architecture uses:

* Timer-based event loop integration (15 FPS polling)
* Platform abstraction layer for Windows/macOS
* Central widget manager with registry pattern
* Window wrapping approach (Blender window becomes Qt foreign window)

---

## Strengths

> [!success] **Key Wins**
> * **Clean Platform Abstraction:** The `blender_applications/` module hierarchy is well-designed with a clear base class interface.
> * **Practical Problem Solving:** Deep understanding of real-world issues (e.g., the Windows modifier key fix in `focus.py`).
> * **Simple Public API:** Excellent developer experience. Example:
> ```python
> main_window = QApplication.instance().blender_widget
> dlg = MyDialog(main_window)
> dlg.show()
> 
> ```
> 
> 
> 
> 

---

## Architectural Concerns

### Dependency & State

> [!warning]- **PySide2 vs [[PySide6]] Confusion**
> **Critical Issue:** Documentation says "PySide6" but code imports PySide2.
> * `README.md` states "PySide6 widget support"
> * `setup.py` lists PySide2 as dependency.
> * Code uses `from PySide2.QtWidgets import ...`
> 
> 

> [!caution] **Global State Management**
> `widget_manager.py` uses a module-level list for widget tracking (`_widget_data = []`).
> * **Risks:** Not thread-safe, hard to test, implicit state sharing.
> * **Recommendation:** Refactor to a [[singleton]] class or instance managed by `BlenderApplication`.
> 
> 

### Performance & Stability

* **Polling-Based Focus Detection:** A 15 FPS timer constantly checks window focus. This introduces CPU overhead and ~66ms latency.
* **Incomplete Error Handling:** Silent `RuntimeError` catches in `widget_manager.py` make debugging disappearances nearly impossible.
* **Unimplemented Unregister:** `unregister()` does not clean up widgets or the `QApplication`, leading to memory leaks.

---

## Code Quality & Maintenance

### Testing & Linting

* **Missing Tests:** No `tests/` directory or CI workflow.
* **Linting Inconsistencies:** `.pylintrc` is configured but many rules are disabled; Black and Pylint character limits conflict.
* **Type Hints:** Missing entirely, limiting IDE autocomplete and contributor clarity.

### Platform Support

* **Linux Support:** Currently returns `None` in `__init__.py`. Should either be implemented or explicitly raise a `NotImplementedError`.
* **Windows Issues:** The "stuck modifier keys" bug remains partially unresolved.

---

## Documentation & DX

* **API Documentation:** Docstrings are often placeholders (e.g., `"TODO update the docs here"`).
* **Environment Variables:** Details are hidden in the Wiki rather than the README.
* **Version Mismatch:** `bl_info` (1.0), `setup.py` (1.1.0), and Releases (2.0.1) are out of sync.

---

## Recommendations Roadmap

### Priority 1: Critical

* [ ] **Fix PySide2/6 confusion:** Align docs with actual dependencies.
* [ ] **Synchronize Versions:** Establish a single source of truth for versioning.
* [ ] **Error Handling:** Add clear initialization failure messages.
* [ ] **Linux Status:** Clearly document as unsupported or implement.

### Priority 2: Important

* [ ] **Add Basic Tests:** Smoke tests for widget registration.
* [ ] **Partial Cleanup:** Implement widget destruction in `unregister()`.
* [ ] **Type Hints:** Add types to the public API.
* [ ] **Logging:** Implement a debug mode for troubleshooting.

### Priority 3: Enhancement

* [ ] **Refactor Global State:** Move to a managed singleton.
* [ ] **Event-driven Focus:** Replace polling with OS-level event hooks.
* [ ] **Standardize Docs:** Use Google/NumPy style docstrings.

---

## Summary Assessment

**Grade: B+**
The project solves a difficult problem with an elegant API and solid platform abstraction. However, it requires polish in **lifecycle management**, **testing**, and **documentation consistency** to be considered maintainable for the long term.

**Navigation:**

* [[#Overview|Top]]
* [[#Strengths|Strengths]]
* [[#Architectural Concerns|Technical Debt]]
* [[#Recommendations Roadmap|Action Items]]
