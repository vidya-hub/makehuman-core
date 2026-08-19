"""Headless stand-in for MakeHuman's global application object (``G.app``).

The vendored core reads a small, well-defined set of attributes off ``G.app``:

- ``selectedHuman`` -- the current Human
- ``saveHandlers`` (list) / ``loadHandlers`` (dict) -- the .mhm persistence hooks
  that plugins normally register (re-homed here via :mod:`mhcore.handlers`)
- ``modelCamera`` -- only for the ``camera`` line in a saved .mhm
- ``progress()`` / ``redraw()`` -- GUI callbacks, no-ops here
- ``settings`` -- a plain dict of settings with ``getSetting``/``setSetting``

Reference touch-points: apps/human.py save()/load(), core/events3d.py,
shared/progress.py.
"""

from __future__ import annotations


class DummyCamera:
    """Minimal camera; only used to (de)serialize the .mhm ``camera`` line."""

    def __init__(self):
        self._rotation = [0.0, 0.0, 0.0]
        self.translation = [0.0, 0.0, 0.0]
        self.zoomFactor = 1.0

    def getRotation(self):
        return list(self._rotation)

    def setRotation(self, rot):
        self._rotation = list(rot)

    def addRotation(self, axis, amount):
        self._rotation[axis] += amount

    def setZoomFactor(self, z):
        self.zoomFactor = z


class HeadlessApp:
    """Drop-in replacement for MHApplication, sufficient for the core pipeline."""

    def __init__(self):
        self.selectedHuman = None
        self.modelCamera = DummyCamera()

        # .mhm persistence hook registries (populated by mhcore.handlers).
        self.saveHandlers = []          # list of callables(human, file)
        self.loadHandlers = {}          # keyword -> callable(human, words, strict)

        # Settings store. Defaults chosen to keep the core path quiet.
        self.settings = {
            "realtimeUpdates": False,
            "cameraAutoZoom": False,
            "preloadTargets": False,
            "useNormals": False,
        }

    # -- GUI callbacks (no-ops) --------------------------------------------
    def redraw(self, *args, **kwargs):
        return None

    def progress(self, *args, **kwargs):
        return None

    def status(self, *args, **kwargs):
        return None

    def statusPersist(self, *args, **kwargs):
        return None

    # -- settings ----------------------------------------------------------
    def getSetting(self, name):
        return self.settings.get(name)

    def setSetting(self, name, value):
        self.settings[name] = value

    def addSetting(self, name, value):
        self.settings.setdefault(name, value)

    # -- .mhm handler registration (mirrors MHApplication API exactly) -----
    def addSaveHandler(self, handler, priority=None):
        # saveHandlers is a flat list of callables(human, file); priority is
        # positional, matching core/mhmain.py.
        if priority is None:
            self.saveHandlers.append(handler)
        else:
            self.saveHandlers.insert(priority, handler)

    def addLoadHandler(self, keyword, handler):
        self.loadHandlers[keyword] = handler

    def getLoadHandler(self, keyword):
        return self.loadHandlers.get(keyword, None)

    # -- undo/redo no-ops (some setters call these) ------------------------
    def do(self, action):
        # Execute the action immediately without an undo stack.
        if hasattr(action, "do"):
            return action.do()
        return None

    def clearUndoRedo(self):
        return None
