from . import utils
from . import gui
from electroncash import WalletStorage, Wallet
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _
from .custom_objc import *
import time
import html
from .uikit_bindings import *
from electroncash.networks import NetworkConstants
from electroncash.address import Address, ScriptOutput
from electroncash import bitcoin
import re
from decimal import Decimal
from .feeslider import FeeSlider
from .amountedit import BTCAmountEdit

RE_ALIAS = '^(.*?)\s*\<([1-9A-Za-z]{26,})\>$'

   
class SendVC(UIViewController):
    stuff = objc_property() # an NSArray of stuff to display
    qr = objc_property()
    qrvc = objc_property()
    qrScanErr = objc_property()
    amountSats = objc_property()
    feeSats = objc_property()
    
    @objc_method
    def init(self):
        self = ObjCInstance(send_super(self, 'init'))
        self.stuff = []
        self.title = _("Send")
        self.qrScanErr = False
        self.amountSats = 0        
        self.feeSats = None  # None ok on this one
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.stuff = None
        self.view = None
        self.qrScanErr = None
        self.amountSats = None
        self.feeSats = None
        send_super(self, 'dealloc')

    @objc_method
    def didRotateFromInterfaceOrientation_(self, o : int) -> None:
        pass
    
    @objc_method
    def reader_didScanResult_(self, reader, result) -> None:
        utils.NSLog("Reader data = '%s'",str(result))
        # TODO: check result here..
        self.checkQRData_(result)
        if self.qrScanErr:
            if type(self.qrScanErr) is int and self.qrScanErr == 2:
                title = _("Unsupported QR Code")
                message = _("The QR code contains multiple outputs. At this time only a single output is supported.\nPlease try again.")
            else:
                title = _("Invalid QR Code")
                message = _("The QR code does not appear to be a valid BCH address or payment request.\nPlease try again.")
            reader.stopScanning()
            gui.ElectrumGui.gui.show_error(
                title = title,
                message = message,
                onOk = lambda: reader.startScanning()
            )
            self.qrScanErr = False
        else:
            self.readerDidCancel_(reader)
             
    @objc_method
    def readerDidCancel_(self, reader) -> None:
        if reader is not None: reader.stopScanning()
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
        
        # Pay To text edit
        tedit = self.view.viewWithTag_(115)
        tedit.delegate = self

        # Amount (BCH) label
        lbl = self.view.viewWithTag_(200)
        
        # Input amount text field
        tedit = self.view.viewWithTag_(210)
        tedit.delegate = self # Amount
        
        lbl = self.view.viewWithTag_(220)
        lbl.text = _("Description")
        
        # Description text field
        tedit = self.view.viewWithTag_(230)
        tedit.delegate = self
        
        but = self.view.viewWithTag_(1090)
        but.setTitle_forState_(_("Max"), UIControlStateNormal)
        but.addTarget_action_forControlEvents_(self, SEL(b'onMaxBut:'), UIControlEventPrimaryActionTriggered)
        
        but = self.view.viewWithTag_(1100)
        but.setTitle_forState_(_("Clear"), UIControlStateNormal)
        but.addTarget_action_forControlEvents_(self, SEL(b'clear'), UIControlEventPrimaryActionTriggered)
        
        but = self.view.viewWithTag_(1110)
        but.setTitle_forState_(_("Preview"), UIControlStateNormal)
        
        but = self.view.viewWithTag_(1120)
        but.setTitle_forState_(_("Send"), UIControlStateNormal)

        # Fee Label
        lbl = self.view.viewWithTag_(300)
        lbl.text = _("Fee")

        tedit = self.view.viewWithTag_(330)
        tedit.placeholder = _("Fee manual edit")
        tedit.delegate = self
        def onManualFee(t : ObjCInstance) -> None:
            print("On Manual fee %s, %s satoshis"%(str(t.text),str(t.getAmount())))
            self.feeSats = t.getAmount()
        utils.add_callback(tedit, 'textChanged', onManualFee)

        # Error Label
        lbl = self.view.viewWithTag_(404)
        lbl.text = _("")

        tedit = self.view.viewWithTag_(230)
        tedit.placeholder = _("Description of the transaction (not mandatory).")
        
        # Check for QRCode availability and if not available, destroy the button
        but = self.view.viewWithTag_(150)
        but.addTarget_action_forControlEvents_(self, SEL(b'onQRBut:'), UIControlEventPrimaryActionTriggered)
   
        feelbl = self.view.viewWithTag_(320)  
        slider = self.view.viewWithTag_(310)
        def sliderCB(dyn : bool, pos : int, fee_rate : int) -> None:
            txt = " ".join(str(slider.getToolTip(pos,fee_rate)).split("\n"))
            feelbl.text = txt
            #print("testcb: %d %d %d.. tt='%s'"%(int(dyn), pos, fee_rate,txt))
        utils.add_callback(slider, 'callback', sliderCB)
        
    @objc_method
    def viewDidLoad(self) -> None:
        self.clear()

    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(self, 'viewWillAppear:', animated, argtypes=[c_bool])
        parent = gui.ElectrumGui.gui

        # redo amount if prefs changed
        tf = self.view.viewWithTag_(210)
        tf.text = parent.format_amount(self.amountSats if self.amountSats is not None else 0)        
        # redo amount label if prefs changed
        lbl = self.view.viewWithTag_(200)
        lbl.text = (_("Amount") + (" ({})")).format(parent.base_unit())
        # Placeholder for amount
        tedit = self.view.viewWithTag_(210)
        tedit.placeholder = (_("Input amount") + " ({})").format(parent.base_unit())
        tedit.delegate = self # Amount
        # fee amount label
        lbl = self.view.viewWithTag_(320)
        lbl.text = self.view.viewWithTag_(310).getToolTip(-1,-1)
        # Manual edit .. re-set the amount in satoshis from our cached value, in case they changed units in the prefs screen
        tedit = self.view.viewWithTag_(330)
        tedit.setAmount_(self.feeSats)
        # fee manual edit unit
        lbl = self.view.viewWithTag_(340)
        lbl.text = (parent.base_unit())

        #lbl.text = "{} {}".format(parent.format_amount(self.feeSats),parent.base_unit())
        self.onPayTo_message_amount_(None,None,None) # does some validation
        
    @objc_method
    def viewWillDisappear_(self, animated: bool) -> None:
        send_super(self, 'viewWillDisappear:', animated, argtypes=[c_bool])
        parent = gui.ElectrumGui.gui
        # Manual edit .. re-call the numify method, applying current units to fee
        tedit = self.view.viewWithTag_(330)
        self.feeSats = tedit.getAmount()
        

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
            self.qrScanErr = False
            pass

    @objc_method
    def textFieldDidBeginEditing_(self, tf) -> None:
        self.view.viewWithTag_(404).text = ""

    @objc_method
    def textFieldShouldEndEditing_(self, tf : ObjCInstance) -> bool:
        print('textFieldShouldEndEditing %d'%tf.tag)
        self.validateForm()
        return True
        
    @objc_method
    def textFieldShouldReturn_(self, tf : ObjCInstance) -> bool:
        print('textFieldShouldReturn %d'%tf.tag)
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def onPayTo_message_amount_(self, address, message, amount) -> None:
        # address
        tf = self.view.viewWithTag_(115)
        tfAddr = tf
        tf.text = str(address) if address is not None else tf.text
        tf.resignFirstResponder() # just in case
        # label
        tf = self.view.viewWithTag_(230)
        tf.text = str(message) if message is not None else tf.text
        tf.resignFirstResponder()
        # amount
        c, u, x = gui.ElectrumGui.gui.wallet.get_balance()
        if amount == "!":
            amount = c+u
        tf = self.view.viewWithTag_(210)
        self.amountSats = int(amount) if type(amount) in [int,float] else self.amountSats
        tf.text = gui.ElectrumGui.gui.format_amount(self.amountSats)
        tf.resignFirstResponder()
        self.qrScanErr = False
        errLbl = self.view.viewWithTag_(404)
        self.view.viewWithTag_(1120).enabled = False
        self.view.viewWithTag_(1110).enabled = False
        try:
            print("wallet balance: %f  amountSats: %f"%(float(c+u),float(self.amountSats)))
            if self.amountSats > c+u:
                errLbl.text = _("Insufficient funds")
                raise Exception()
            elif self.amountSats <= 0:
                errLbl.text = ""
                raise Exception()
            Parser().parse_address(tfAddr.text)
            self.view.viewWithTag_(1120).enabled = True
            self.view.viewWithTag_(1110).enabled = True
            errLbl.text = ""
        except:
            pass
        utils.NSLog("OnPayTo %s %s %s",str(address), str(message), str(amount))
        
    @objc_method
    def onMaxBut_(self, but : ObjCInstance) -> None:
        c, u, x = gui.ElectrumGui.gui.wallet.get_balance()
        self.onPayTo_message_amount_(None,None,c+u)
        
    @objc_method
    def clear(self) -> None:
        # address
        tf = self.view.viewWithTag_(115)
        tf.text = ""
        # label
        tf = self.view.viewWithTag_(230)
        tf.text = ""
        # slider
        slider = self.view.viewWithTag_(310)
        slider.setValue_animated_(slider.minimumValue,True)
        slider.onMoved()
        # manual edit fee
        tf = self.view.viewWithTag_(330)
        tf.setAmount(None)
        # self.amountSats set below..
        self.onPayTo_message_amount_(None,None,0)
        
    @objc_method
    def validateForm(self) -> bool:
        errLbl = self.view.viewWithTag_(404)
        addrTf = self.view.viewWithTag_(115)
        sendBut = self.view.viewWithTag_(1120)
        previewBut = self.view.viewWithTag_(1110)
        amountTf = self.view.viewWithTag_(210)
        parser = Parser()

        errLbl.text = ""
        
        amt = None
        
        class HasErrors(Exception):
            pass
        
        try:
            
            try:
                parser.parse_address(addrTf.text)
            except:
                errLbl.text = _("Invalid Address")
                raise HasErrors("")
            
            try:
                amt = parser.parse_amount(amountTf.text)
            except:
                errLbl.text = _("Invalid Amount")
                raise HasErrors("")
            
            c, u, x = gui.ElectrumGui.gui.wallet.get_balance()
            if c+u < amt:
                errLbl.text = _("Insufficient funds")
                raise HasErrors("")

        except HasErrors as e:
            #print ("HasErrors...")
            previewBut.enabled = False
            sendBut.enabled = False
            return False
        
        self.onPayTo_message_amount_(None,None,amt)
        return True

    @objc_method
    def checkQRData_(self, text) -> None:
        self.qrScanErr = False
        scan_f =  gui.ElectrumGui.gui.pay_to_URI
        parser = Parser()

        #self.errors = []
        errors = []
        #if self.is_pr:
        #    return
        # filter out empty lines
        lines = text.split("\n")
        lines = [i for i in lines if i]
        outputs = []
        total = 0
        #self.payto_address = None
        payto_address = None
        if len(lines) == 1:
            data = lines[0]
            if data.lower().startswith(NetworkConstants.CASHADDR_PREFIX + ":"):
                def errFunc(): self.qrScanErr = True
                scan_f(data, errFunc)
                return
            try:
                #self.payto_address = self.parse_output(data)
                payto_address = parser.parse_output(data)
            except:
                pass
            #if self.payto_address:
            if payto_address and len(payto_address) and isinstance(payto_address[1], Address):
                #self.win.lock_amount(False)
                #print("LOCK AMOUNT = False")
                
                try:
                    #self.onPayTo_message_amount_(payto_address[1].to_ui_string(), None, None)
                    self.onPayTo_message_amount_(data, None, None)
                    return
                except Exception as e:
                    print("EXCEPTION -- %s"%str(e))
                    pass

        is_max = False
        for i, line in enumerate(lines):
            try:
                _type, to_address, amount = parser.parse_address_and_amount(line)
            except:
                #self.errors.append((i, line.strip()))
                errors.append((i, line.strip()))
                continue

            outputs.append((_type, to_address, amount))
            if amount == '!':
                is_max = True
            else:
                total += amount

        #self.win.is_max = is_max
        #self.outputs = outputs
        #self.payto_address = None

        #if self.win.is_max:
        #    self.win.do_update_fee()
        #else:
        #    self.amount_edit.setAmount(total if outputs else None)
        #    self.win.lock_amount(total or len(lines)>1)
        if len(errors):
            self.qrScanErr = True
        elif len(outputs) != 1:
            self.qrScanErr = 2
        else:
            print("onCheckPayToText.. last clause")
            self.onPayTo_message_amount_(outputs[0][1].to_ui_string(),"",outputs[0][2])
        utils.NSLog("onCheckPayToText_ result: is_max=%s outputs=%s total=%s errors=%s",str(is_max),str(outputs),str(total),str(errors))

class Parser:
    def parse_address_and_amount(self, line):
        x, y = line.split(',')
        out_type, out = self.parse_output(x)
        amount = self.parse_amount(y)
        return out_type, out, amount

    def parse_output(self, x):
        try:
            address = self.parse_address(x)
            return bitcoin.TYPE_ADDRESS, address
        except:
            return bitcoin.TYPE_SCRIPT, ScriptOutput.from_string(x)

    def parse_address(self, line):
        r = line.strip()
        m = re.match(RE_ALIAS, r)
        address = m.group(2) if m else r
        return Address.from_string(address)

    def parse_amount(self, x):
        if x.strip() == '!':
            return '!'
        p = pow(10, gui.ElectrumGui.gui.get_decimal_point())
        return int(p * Decimal(x.strip()))
