#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Asset operations for the MakeHuman server socket bridge.

Wraps the mhapi.assets namespace so a socket client (for example the
standalone MCP server) can discover installed assets and equip / unequip
clothes, hair, eyebrows, eyelashes and skins.

All handlers follow the AbstractOp convention: they receive (conn, jsonCall)
and set jsonCall.data, or call jsonCall.setError(...) on failure.
"""

import material

from .abstractop import AbstractOp


class SocketAssetOps(AbstractOp):

    def __init__(self, sockettaskview):
        super().__init__(sockettaskview)

        # Discovery (return lists of full paths to installed assets)
        self.functions["getAvailableClothes"] = self.getAvailableClothes
        self.functions["getAvailableHair"] = self.getAvailableHair
        self.functions["getAvailableEyebrows"] = self.getAvailableEyebrows
        self.functions["getAvailableEyelashes"] = self.getAvailableEyelashes
        self.functions["getAvailableSkins"] = self.getAvailableSkins

        # Equip / unequip
        self.functions["equipClothes"] = self.equipClothes
        self.functions["unequipClothes"] = self.unequipClothes
        self.functions["unequipAllClothes"] = self.unequipAllClothes
        self.functions["equipHair"] = self.equipHair
        self.functions["unequipHair"] = self.unequipHair
        self.functions["equipEyebrows"] = self.equipEyebrows
        self.functions["unequipEyebrows"] = self.unequipEyebrows
        self.functions["equipEyelashes"] = self.equipEyelashes
        self.functions["unequipEyelashes"] = self.unequipEyelashes
        self.functions["setSkin"] = self.setSkin

        # Query what is currently equipped
        self.functions["getEquippedClothes"] = self.getEquippedClothes
        self.functions["getEquippedHair"] = self.getEquippedHair
        self.functions["getEquippedEyebrows"] = self.getEquippedEyebrows
        self.functions["getEquippedEyelashes"] = self.getEquippedEyelashes

    # -- discovery ----------------------------------------------------------

    def getAvailableClothes(self, conn, jsonCall):
        jsonCall.data = (self.api.assets.getAvailableSystemClothes() +
                         self.api.assets.getAvailableUserClothes())

    def getAvailableHair(self, conn, jsonCall):
        jsonCall.data = (self.api.assets.getAvailableSystemHair() +
                         self.api.assets.getAvailableUserHair())

    def getAvailableEyebrows(self, conn, jsonCall):
        jsonCall.data = (self.api.assets.getAvailableSystemEyebrows() +
                         self.api.assets.getAvailableUserEyebrows())

    def getAvailableEyelashes(self, conn, jsonCall):
        jsonCall.data = (self.api.assets.getAvailableSystemEyelashes() +
                         self.api.assets.getAvailableUserEyelashes())

    def getAvailableSkins(self, conn, jsonCall):
        jsonCall.data = (self.api.assets.getAvailableSystemSkins() +
                         self.api.assets.getAvailableUserSkins())

    # -- equip / unequip ----------------------------------------------------

    def equipClothes(self, conn, jsonCall):
        self.api.assets.equipClothes(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def unequipClothes(self, conn, jsonCall):
        self.api.assets.unequipClothes(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def unequipAllClothes(self, conn, jsonCall):
        self.api.assets.unequipAllClothes()
        jsonCall.setData("OK")

    def equipHair(self, conn, jsonCall):
        self.api.assets.equipHair(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def unequipHair(self, conn, jsonCall):
        self.api.assets.unequipHair(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def equipEyebrows(self, conn, jsonCall):
        self.api.assets.equipEyebrows(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def unequipEyebrows(self, conn, jsonCall):
        self.api.assets.unequipEyebrows(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def equipEyelashes(self, conn, jsonCall):
        self.api.assets.equipEyelashes(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def unequipEyelashes(self, conn, jsonCall):
        self.api.assets.unequipEyelashes(jsonCall.getParam("path"))
        jsonCall.setData("OK")

    def setSkin(self, conn, jsonCall):
        """Set the body skin from a MHMAT material file path."""
        path = jsonCall.getParam("path")
        mat = material.fromFile(path)
        self.human.setMaterial(mat)
        jsonCall.setData("OK")

    # -- query --------------------------------------------------------------

    def getEquippedClothes(self, conn, jsonCall):
        jsonCall.data = self.api.assets.getEquippedClothes()

    def getEquippedHair(self, conn, jsonCall):
        jsonCall.data = self.api.assets.getEquippedHair()

    def getEquippedEyebrows(self, conn, jsonCall):
        jsonCall.data = self.api.assets.getEquippedEyebrows()

    def getEquippedEyelashes(self, conn, jsonCall):
        jsonCall.data = self.api.assets.getEquippedEyelashes()
