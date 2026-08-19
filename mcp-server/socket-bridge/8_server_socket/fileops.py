#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
File operations for the MakeHuman server socket bridge.

Lets a socket client save / load the native .mhm character format and export
the current character to the common 3D interchange formats via mhapi.exports.

All handlers follow the AbstractOp convention: they receive (conn, jsonCall)
and set jsonCall.data, or call jsonCall.setError(...) on failure.
"""

from core import G

from .abstractop import AbstractOp


class SocketFileOps(AbstractOp):

    def __init__(self, sockettaskview):
        super().__init__(sockettaskview)
        self.functions["saveMHM"] = self.saveMHM
        self.functions["loadMHM"] = self.loadMHM
        self.functions["exportOBJ"] = self.exportOBJ
        self.functions["exportFBX"] = self.exportFBX
        self.functions["exportDAE"] = self.exportDAE
        self.functions["exportMHX2"] = self.exportMHX2

    def saveMHM(self, conn, jsonCall):
        """Save the current character as a .mhm file at the given path.

        Uses Human.save() directly (rather than guisave.saveMHM) so that it
        works even when the window is minimized -- it still runs the full
        save-handler chain (materials, skeleton, clothes, ...) but skips the
        screen-grab thumbnail.
        """
        path = jsonCall.getParam("path")
        if not path:
            jsonCall.setError("Missing 'path' parameter")
            return
        if not path.lower().endswith(".mhm"):
            path += ".mhm"
        self.human.save(path)
        jsonCall.setData(path)

    def loadMHM(self, conn, jsonCall):
        """Load a .mhm file into the current character."""
        path = jsonCall.getParam("path")
        if not path:
            jsonCall.setError("Missing 'path' parameter")
            return
        G.app.loadHumanMHM(path)
        jsonCall.setData("OK")

    def _useExportsDir(self, jsonCall):
        # Default False so the client's full path is honoured; pass
        # useExportsDir=true to drop the file in MakeHuman's exports folder.
        return bool(jsonCall.getParam("useExportsDir"))

    def exportOBJ(self, conn, jsonCall):
        self.api.exports.exportAsOBJ(jsonCall.getParam("path"), self._useExportsDir(jsonCall))
        jsonCall.setData("OK")

    def exportFBX(self, conn, jsonCall):
        self.api.exports.exportAsFBX(jsonCall.getParam("path"), self._useExportsDir(jsonCall))
        jsonCall.setData("OK")

    def exportDAE(self, conn, jsonCall):
        self.api.exports.exportAsDAE(jsonCall.getParam("path"), self._useExportsDir(jsonCall))
        jsonCall.setData("OK")

    def exportMHX2(self, conn, jsonCall):
        exporter = self.api.exports.getMHX2Exporter()
        if exporter is None:
            jsonCall.setError("MHX2 exporter is not installed")
            return
        self.api.exports.exportAsMHX2(jsonCall.getParam("path"), self._useExportsDir(jsonCall))
        jsonCall.setData("OK")
