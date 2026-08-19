#!/usr/bin/python3
# -*- coding: utf-8 -*-

from .abstractop import AbstractOp

class SocketModifierOps(AbstractOp):

    def __init__(self, sockettaskview):
        super().__init__(sockettaskview)
        self.functions["applyModifier"] = self.applyModifier
        self.functions["applyTarget"] = self.applyTarget
        self.functions["getAppliedTargets"] = self.getAppliedTargets
        self.functions["getAvailableModifierNames"] = self.getAvailableModifierNames
        self.functions["setGender"] = self.setGender
        self.functions["setAge"] = self.setAge
        self.functions["setWeight"] = self.setWeight
        self.functions["setMuscle"] = self.setMuscle
        self.functions["setHeight"] = self.setHeight

    def getAvailableModifierNames(self,conn,jsonCall):
        jsonCall.data = self.api.modifiers.getAvailableModifierNames()

    def getAppliedTargets(self,conn,jsonCall):
        jsonCall.data = self.api.modifiers.getAppliedTargets()

    def applyModifier(self,conn,jsonCall):
        modifierName = jsonCall.getParam("modifier")
        power = float(jsonCall.getParam("power"))
        modifier = self.api.internals.getHuman().getModifier(modifierName)

        if not modifier:
            jsonCall.setError("No such modifier")
            return

        self.api.modifiers.applyModifier(modifierName,power,True)
        jsonCall.setData("OK")

    def applyTarget(self,conn,jsonCall):
        targetName = jsonCall.getParam("target")
        power = float(jsonCall.getParam("power"))
        self.api.modifiers.applyTarget(targetName, power, True)
        jsonCall.setData("OK")

    def _macroValue(self, jsonCall):
        """Read and clamp a macro 'value' param to the 0.0 - 1.0 range."""
        value = float(jsonCall.getParam("value"))
        if value < 0.0:
            value = 0.0
        if value > 1.0:
            value = 1.0
        return value

    def setGender(self,conn,jsonCall):
        self.api.modifiers.setGender(self._macroValue(jsonCall))
        jsonCall.setData("OK")

    def setAge(self,conn,jsonCall):
        self.api.modifiers.setAge(self._macroValue(jsonCall))
        jsonCall.setData("OK")

    def setWeight(self,conn,jsonCall):
        self.api.modifiers.setWeight(self._macroValue(jsonCall))
        jsonCall.setData("OK")

    def setMuscle(self,conn,jsonCall):
        self.api.modifiers.setMuscle(self._macroValue(jsonCall))
        jsonCall.setData("OK")

    def setHeight(self,conn,jsonCall):
        self.api.modifiers.setHeight(self._macroValue(jsonCall))
        jsonCall.setData("OK")



