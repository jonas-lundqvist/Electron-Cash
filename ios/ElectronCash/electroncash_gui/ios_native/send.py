from . import utils
from . import gui
from . import heartbeat
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _
from .custom_objc import *
import time
import html
from .uikit_bindings import *

class SendVC(UIViewController):
    stuff = objc_property() # an NSArray of stuff to display
    qr = objc_property()
    qrvc = objc_property()
    
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
    def reader_didScanResult_(self, reader, result) -> None:
        print("Reader result=%s"%(str(result)))
        # TODO: check result here..
        tedit = self.view.viewWithTag_(115)
        tedit.text = result
        self.readerDidCancel_(reader)

 
    @objc_method
    def readerDidCancel_(self, reader) -> None:
        self.dismissViewControllerAnimated_completion_(True, None)
        self.qr = None
        self.qrvc = None
        
        
    @objc_method
    def loadView(self) -> None:
        objs = NSBundle.mainBundle.loadNibNamed_owner_options_("Send",self,None)
        assert objs is not None and len(objs)
        self.view = objs[0]
        contentView = self.view.viewWithTag_(100)
        
        # Apply translations and other stuff to UI text...
        parent = gui.ElectrumGui.gui

        lbl = self.view.viewWithTag_(110)
        lbl.text = _("Pay to")

        lbl = self.view.viewWithTag_(200)
        lbl.text = (_("Amount") + (" ({})")).format(parent.base_unit())
        
        tedit = self.view.viewWithTag_(210)
        tedit.placeholder = (_("Input amount") + " ({})").format(parent.base_unit())
        
        lbl = self.view.viewWithTag_(220)
        lbl.text = _("Description")
        
        but = self.view.viewWithTag_(1090)
        but.setTitle_forState_(_("Max"), UIControlStateNormal)
        
        but = self.view.viewWithTag_(1100)
        but.setTitle_forState_(_("Clear"), UIControlStateNormal)
        
        but = self.view.viewWithTag_(1110)
        but.setTitle_forState_(_("Preview"), UIControlStateNormal)
        
        but = self.view.viewWithTag_(1120)
        but.setTitle_forState_(_("Send"), UIControlStateNormal)

        #tedit = self.view.viewWithTag_(230)
        #tedit.placeholder = _("Description of the transaction (not mandatory).")
        
        # Check for QRCode availability and if not available, destroy the button
        but = self.view.viewWithTag_(150)
        but.addTarget_action_forControlEvents_(self, SEL(b'onQRBut:'), UIControlEventPrimaryActionTriggered)

    @objc_method
    def onQRBut_(self, but):
        if not QRCodeReader.isAvailable:
            utils.show_alert(self, _("QR Not Avilable"), _("The camera is not available for reading QR codes"))
        else:
            self.qr = QRCodeReader.new().autorelease()
            self.qrvc = QRCodeReaderViewController.readerWithCancelButtonTitle_codeReader_startScanningAtLoad_showSwitchCameraButton_showTorchButton_("Cancel",self.qr,True,True,True)
            self.qrvc.modalPresentationStyle = UIModalPresentationFormSheet
            self.qrvc.delegate = self
            self.presentViewController_animated_completion_(self.qrvc, True, None)
            pass
