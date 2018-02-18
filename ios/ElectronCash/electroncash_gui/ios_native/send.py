from . import utils
from . import gui
from . import heartbeat
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
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
        self.title = "Send"
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.stuff = None
        self.view = None
        send_super(self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        self.view = UIView.alloc().init().autorelease()
        lbl = UILabel.alloc().init().autorelease()
        lbl.text = "Send UI will go here"
        lbl.adjustsFontSizeForWidth = True
        lbl.numberOfLines = 2
        w = UIScreen.mainScreen.bounds.size.width
        rect = CGRectMake(10,100,w,80)
        lbl.frame = rect
        self.view.addSubview_(lbl)
