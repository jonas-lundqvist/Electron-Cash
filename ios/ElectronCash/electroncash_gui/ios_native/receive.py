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
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("Receive",self,None)
        assert objs is not None and len(objs)
        for i,o in enumerate(objs):
            if o.objc_class is UIScrollView:
                self.view = o
            elif o.objc_class is UITapGestureRecognizer:
                o.addTarget_action_(self, SEL('onAddressTap:'))
                
        if not self.view:
            raise Exception("Could not build view -- Receive.xib is missing a UIScrollView as a root object!")
    
    @objc_method
    def viewDidLoad(self) -> None:
        # do setup...
        print("viewDidLoad")
        
    
    @objc_method
    def onAddressTap_(self, uigr : ObjCInstance) -> None:
        lbl = uigr.view
        print("UNIMPLEMENTED lbl=%s"%lbl.text)
