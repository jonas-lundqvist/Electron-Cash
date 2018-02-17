#!/usr/bin/env python3
#

from .uikit_bindings import *
from . import gui
import ElectronCash.app

class PythonAppDelegate(UIResponder):
    @objc_method
    def applicationDidBecomeActive(self) -> None:
        print("App became active.")

    @objc_method
    def application_didFinishLaunchingWithOptions_(self, application, launchOptions) -> bool:
        print("App finished launching.")

        ElectronCash.app.main()

        return False

    @objc_method
    def application_didChangeStatusBarOrientation_(self, application, oldStatusBarOrientation: int) -> None:
        print("ROTATED", oldStatusBarOrientation)
        gui.ElectrumGui.gui.on_rotated()
