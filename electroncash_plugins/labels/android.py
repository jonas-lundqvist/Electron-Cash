from electroncash.plugins import hook

from .labels import LabelsPlugin

class Plugin(LabelsPlugin):
    def __init__(self, *args):
        LabelsPlugin.__init__(self, *args)

    @hook
    def on_new_window(self, window):
        self.start_wallet(window.wallet)

    @hook
    def on_close_window(self, window):
        self.stop_wallet(window.wallet)
