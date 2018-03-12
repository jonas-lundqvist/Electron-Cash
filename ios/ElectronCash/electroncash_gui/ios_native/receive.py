from . import utils
from . import gui
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
import html
from .uikit_bindings import *

class ReceiveVC(UIViewController):
    stuff = objc_property() # an NSArray of stuff to display
    
    @objc_method
    def init(self):
        self = ObjCInstance(send_super(__class__, self, 'init'))
        self.stuff = []
        self.title = _("Receive")
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.stuff = None
        self.view = None
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def didRotateFromInterfaceOrientation_(self, o : int) -> None:
        pass

    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("Receive",self,None)
        assert objs is not None and len(objs)
        self.view = objs[0]
        v = self.view.viewWithTag_(100)
