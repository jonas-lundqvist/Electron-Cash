from . import utils
from . import gui
from . import heartbeat
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _
import time
import html

try:
    from .uikit_bindings import *
except Exception as e:
    sys.exit("Error: Could not import iOS libs: %s"%str(e))


class SendVC(UIViewController):
    stuff = objc_property() # an NSArray of stuff to display
    
    @objc_method
    def init(self):
        self = ObjCInstance(send_super(self, 'init'))
        self.stuff = []
        self.title = _("Send")
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.stuff = None
        self.view = None
        send_super(self, 'dealloc')

    @objc_method
    def didRotateFromInterfaceOrientation_(self, o : int) -> None:
        pass
    
    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("Send",self,None)
        assert objs is not None and len(objs)
        self.view = objs[0]
        v = self.view.viewWithTag_(100)
