from electroncash.plugins import hook

from .labels import LabelsPlugin

class Plugin(LabelsPlugin):
    def __init__(self, *args):
        LabelsPlugin.__init__(self, *args)

    @hook
    def start_android_wallet(self, wallet):
        self.start_wallet(wallet)

    @hook
    def stop_android_wallet(self, wallet):
        self.stop_wallet(wallet)
