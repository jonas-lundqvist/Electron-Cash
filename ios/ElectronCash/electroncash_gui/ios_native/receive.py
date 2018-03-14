from . import utils
from . import gui
from .amountedit import BTCAmountEdit, FiatAmountEdit, BTCkBEdit  # Makes sure ObjC classes are imported into ObjC runtime
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
from electroncash.networks import NetworkConstants
from electroncash.address import Address, ScriptOutput
from electroncash import bitcoin
import electroncash.web as web
import time
import html
from .uikit_bindings import *
from decimal import Decimal

def parent():
    return gui.ElectrumGui.gui

def decodeAddress(addr : str) -> Address:
    ret = None
    if addr:
        try:
            # re-encode addr in case they went to/from cashaddr
            ret = Address.from_string(addr)
        except BaseException as e:
            utils.NSLog("Caught exception decoding address %s: %s",addr,str(e))
    return ret

class ReceiveVC(UIViewController):
    ui = objc_property() # a dictionary of string -> ObjCInstance -- all the GUI elements in the form are conveniently found here 
    expiresIdx = objc_property() # the index of their 'expires' pick -- saved for ui translation
    expiresList = objc_property()
    addr = objc_property() # string repr of address
    fxIsEnabled = objc_property()
    lastQRData = objc_property()
    
    @objc_method
    def init(self):
        self = ObjCInstance(send_super(__class__, self, 'init'))
        self.ui = {}
        self.expiresIdx = 0
        self.expiresList =  [
            ['Never', 0],
            ['1 hour', 60*60],
            ['1 day', 24*60*60],
            ['1 week', 7*24*60*60],
        ]
        self.title = _("Receive")
        self.fxIsEnabled = None
        self.addr = None
        self.lastQRData = ""
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.ui = None
        self.expiresList = None
        self.expiresIdx = None
        self.fxIsEnabled = None
        self.addr = None
        self.view = None
        self.lastQRData = None
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
        ui = {}
        v = self.view
        
        ui['addrTit'] = v.viewWithTag_(100)
        ui['addr'] = v.viewWithTag_(110)
        ui['copyBut'] = v.viewWithTag_(120)

        ui['descTit'] = v.viewWithTag_(200)
        ui['desc'] = v.viewWithTag_(210)

        ui['amtTit'] = v.viewWithTag_(300)
        ui['amt'] = v.viewWithTag_(310)
        ui['amtLbl'] = v.viewWithTag_(320)
        ui['amtFiat'] = v.viewWithTag_(330)
        ui['amtFiatLbl'] = v.viewWithTag_(340)
        
        ui['expiresTit'] = v.viewWithTag_(400)
        ui['expiresBut'] = v.viewWithTag_(410)

        ui['saveBut'] = v.viewWithTag_(500)
        ui['newBut'] = v.viewWithTag_(510)
        
        ui['qr'] = v.viewWithTag_(600)
        
        ui['tv'] = v.viewWithTag_(700)
        ui['tv'].delegate = self
        ui['tv'].dataSource = self

        def onAmtChg(amtEdit) -> None:
            print("onAmtChg tag = ", amtEdit.tag)
            if not amtEdit.isModified(): return
            if amtEdit.tag == 310:
                self.updateFXFromAmt()
            elif amtEdit.tag == 330:
                self.updateAmtFromFX()
            self.redoQR()

        utils.add_callback(ui['amt'], 'textChanged', onAmtChg)
        utils.add_callback(ui['amtFiat'], 'textChanged', onAmtChg)

        ui['amt'].delegate = self
        ui['amtFiat'].delegate = self
        ui['desc'].delegate = self

        ui['newBut'].addTarget_action_forControlEvents_(self, SEL(b'clear'), UIControlEventPrimaryActionTriggered)
        ui['saveBut'].addTarget_action_forControlEvents_(self, SEL(b'onSave'), UIControlEventPrimaryActionTriggered)
        ui['copyBut'].addTarget_action_forControlEvents_(self, SEL(b'onCopyBut'), UIControlEventPrimaryActionTriggered)
        ui['expiresBut'].addTarget_action_forControlEvents_(self, SEL(b'showExpiresMenu:'), UIControlEventPrimaryActionTriggered)
        
        self.ui = ns_from_py(ui)

        self.translateUI()
        
    @objc_method
    def translateUI(self) -> None:
        ''' In the future all of our GUI view controllers will implement this method to re-do language-specific text '''
        ui = py_from_ns(self.ui)
        # Setup translation-based stuff
        ui['addrTit'].text = _("Receiving address")
        ui['descTit'].text = _("Description")
        ui['amtTit'].text = _("Requested amount")
        ui['expiresTit'].text = _("Request expires")
        ui['expiresBut'].setTitle_forState_(_(self.expiresList[self.expiresIdx][0]),UIControlStateNormal)
        ui['saveBut'].setTitle_forState_(_("Save"), UIControlStateNormal)
        ui['newBut'].setTitle_forState_(_("New"), UIControlStateNormal)
        
        ui['tv'].reloadData()

    @objc_method
    def refresh(self) -> None:
        if self.ui:
            self.ui['tv'].reloadData()
            self.viewWillAppear_(False)

    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        if not self.ui:
            utils.NSLog("ERROR -- ReceiveVC is missing its self.ui dictionary in viewWillAppear()!! FIXME!")
            return
        ui = py_from_ns(self.ui)
        ui['amtLbl'].text = ui['amt'].baseUnit()
        ui['amtFiatLbl'].text = ui['amtFiat'].baseUnit()
        # Placeholder for amount
        ui['amt'].placeholder = (_("Input amount") + " ({})").format(ui['amt'].baseUnit())
        ui['amtFiat'].placeholder = (_("Input amount") + " ({})").format(ui['amtFiat'].baseUnit())
        ui['amt'].setAmount_(ui['amt'].getAmount()) # redoes decimal point placement
        
        if not self.addr:
            # get an address
            a = parent().wallet.get_receiving_address()
            if a is None:
                parent().show_error(_("Unable to get a receiving address from your wallet!"))
            else:
                self.addr = a.to_ui_string()
        
        if self.addr:
            address = decodeAddress(self.addr)
            if address is not None:
                ui['addr'].text = address.to_ui_string()
                self.addr = address.to_ui_string()
            
        self.fxIsEnabled = parent().daemon.fx and parent().daemon.fx.is_enabled()
        utils.uiview_set_enabled(ui['amtFiat'], self.fxIsEnabled)
        utils.uiview_set_enabled(ui['amtFiatLbl'], self.fxIsEnabled)
        
        self.redoQR()
        self.updateFXFromAmt()
                   
    @objc_method
    def viewWillDisappear_(self, animated : bool) -> None:
        ui = self.ui
        if not ui: return
        self.addr = ui['addr'].text
    
    @objc_method
    def onAddressTap_(self, uigr : ObjCInstance) -> None:
        lbl = uigr.view
        print("UNIMPLEMENTED lbl=%s"%lbl.text)

    @objc_method
    def onCopyBut(self) -> None:
        UIPasteboard.generalPasteboard.string = self.addr
        utils.show_notification(message=_("Text copied to clipboard"))
    
    @objc_method
    def setExpiresByIndex_(self, idx : int) -> None:
        if idx < 0 or idx >= len(self.expiresList): return
        self.expiresIdx = idx
        self.ui['expiresBut'].setTitle_forState_(_(self.expiresList[idx][0]),UIControlStateNormal)
        
        
    @objc_method
    def showExpiresMenu_(self, but : ObjCInstance) -> None:
        expiresList = self.expiresList
        ui = self.ui
        if not ui: return
        def onSelect(idx : int) -> None:
            self.setExpiresByIndex_(idx)
        actions = list(map(lambda x,y: [ _(x[0]), onSelect, y ], expiresList, range(0,len(expiresList))))
        actions.append([_('Cancel')])
        alertvc = utils.show_alert(vc = parent().get_presented_viewcontroller(),
                                   title = ui['expiresTit'].text,
                                   message = _("Select when the payment request should expire"),
                                   actions = actions,
                                   cancel = _('Cancel'),
                                   style = UIAlertControllerStyleActionSheet)    
        
    @objc_method
    def updateFXFromAmt(self) -> None:
        ui = self.ui
        if not ui: return
        if not self.fxIsEnabled:
            ui['amtFiat'].setAmount_(None)
            return
        amount = ui['amt'].getAmount()
        amountFiat = None
        if amount is not None:
            amount = Decimal(pow(10, -8)) * amount
            rate = Decimal(parent().daemon.fx.exchange_rate())
            amountFiat = rate * amount * Decimal(100.0)
        amountFiatOld = ui['amtFiat'].getAmount()
        if amountFiat != amountFiatOld:
            ui['amtFiat'].setAmount_(amountFiat)

    @objc_method
    def updateAmtFromFX(self) -> None:
        ui = self.ui
        if not ui or not self.fxIsEnabled: return
        amountFiat = ui['amtFiat'].getAmount()
        amount = None
        if amountFiat is not None:
            amountFiat = Decimal(amountFiat) / Decimal(100.0)
            rate = parent().daemon.fx.exchange_rate()
            amount = amountFiat/Decimal(rate) * Decimal(pow(10, 8))
        amountOld = ui['amt'].getAmount()
        if amount != amountOld:
            ui['amt'].setAmount_(amount)
    
    @objc_method
    def generatePrURI(self) -> ObjCInstance:
        ui = self.ui
        if not ui: return
        qriv = ui['qr']
        amount = ui['amt'].getAmount()
        message = ui['desc'].text
        print("addr,amount,message=",self.addr,amount,message)
        uri = web.create_URI(decodeAddress(self.addr), amount, message)
        print("uri = ",uri)
        return uri        
        
    @objc_method
    def redoQR(self) -> None:
        ui = self.ui
        if not ui: return
        uri = self.generatePrURI()
        qriv = ui['qr']
        amount = ui['amt'].getAmount()
        message = ui['desc'].text
        utils.uiview_set_enabled(ui['saveBut'],
                                 (amount is not None) or (message != ""))
        if uri != self.lastQRData:
            qriv.image = utils.get_qrcode_image_for_data(uri)
            self.lastQRData = uri
            
    @objc_method
    def clear(self) -> None:
        self.lastQRData = None
        ui = self.ui
        if not ui: return
        ui['amt'].setAmount_(None)
        ui['amtFiat'].setAmount_(None)
        ui['desc'].text = ""
        self.setExpiresByIndex_(0)
        self.redoQR()

    @objc_method
    def onSave(self) -> None:
        if not self.addr:
            parent().show_error(_('No receiving address'))
            return
        ui = self.ui
        if not ui:
            parent().show_error(_('Critical Error'))
            return
        amount = ui['amt'].getAmount()
        message = ui['desc'].text
        if not message and not amount:
            parent().show_error(_('No message or amount'))
            return False
        i = self.expiresIdx
        expiration = list(map(lambda x: x[1], self.expiresList))[i]
        if expiration <= 0: expiration = None
        req = parent().wallet.make_payment_request(decodeAddress(self.addr), amount, message, expiration)
        print(req)
        #parent().wallet.add_payment_request(req, parent().config)
        #self.sign_payment_request(self.receive_address)
        #self.request_list.update()
        #self.address_list.update()
        #self.save_request_button.setEnabled(False)


    ## tf delegate methods
    @objc_method
    def textFieldShouldEndEditing_(self, tf : ObjCInstance) -> bool:
        #print('textFieldShouldEndEditing %d'%tf.tag)
        if tf == self.ui['desc']:
            tf.text = tf.text.strip()
            self.redoQR() # other tf's are handled by other callbacks
        return True
        
    @objc_method
    def textFieldShouldReturn_(self, tf : ObjCInstance) -> bool:
        #print('textFieldShouldReturn %d'%tf.tag)
        tf.resignFirstResponder()
        return True
    
    ## TABLEVIEW related methods.. TODO: implement
    @objc_method
    def numberOfSectionsInTableView_(self, tv) -> int:
        return 1
    
    @objc_method
    def tableView_titleForHeaderInSection_(self, tv : ObjCInstance,section : int) -> ObjCInstance:
        return _("Requests")
            
    @objc_method
    def tableView_numberOfRowsInSection_(self, tv : ObjCInstance, section : int) -> int:
        return 0
 
    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tv, indexPath) -> ObjCInstance:
        return None

    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath) -> None:
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath) -> None:
        pass

