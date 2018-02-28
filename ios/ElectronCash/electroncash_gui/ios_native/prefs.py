from . import utils
from . import gui
from . import heartbeat
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
import html
from .uikit_bindings import *
import electroncash.web as web


SECTION_TITLES = [ 'Fees', 'Transactions', 'Appearance', 'Fiat',
                  #'Identity'
                  ]

TAG_MULTIPLE_CHANGE_CELL = 1337001
TAG_CONTENTVIEW = 100
TAG_BASE_UNIT = 302
TAG_NZ = 303
TAG_BLOCK_EXPLORER = 304
TAG_FIAT_CURRENCY = 401
TAG_FIAT_EXCHANGE = 404

UNITS = { 'BCH': 8, 'mBCH': 5, 'bits' : 2}
UNIT_KEYS = list(UNITS.keys())
UNIT_KEYS.sort(key=lambda x: UNITS[x],reverse=True)


class PrefsVC(UITableViewController):
    
    closeButton = objc_property() # caller sets this
    
    currencies = objc_property() # NSArray of strings...
    exchanges = objc_property() # NSArray of strings...
        
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(self, 'initWithStyle:', UITableViewStyleGrouped, argtypes=[c_int]))
        self.title = _("Preferences")
        self.closeButton = None
        self.currencies = None
        self.exchanges = None
        self.updateCurrencies()
        self.updateExchanges()
        return self
    
    @objc_method
    def initWithStyle_(self, style : int) -> ObjCInstance:
        print("WARNING: PrefsVC doesn't support the initWithStyle: method -- use plain old 'init' instead!")
        assert style == UITableViewStyleGrouped
        return self.init()
        
    @objc_method
    def dealloc(self) -> None:
        self.closeButton = None
        self.currencies = None
        self.exchanges = None
        send_super(self, 'dealloc')

    @objc_method
    def multipleChangeCell(self) -> ObjCInstance:
        if self.viewIfLoaded:
            return self.viewIfLoaded.viewWithTag_(TAG_MULTIPLE_CHANGE_CELL)
        return None

    @objc_method
    def refresh(self):
        try:
            self.refreshControl.endRefreshing()
        except:
            pass
        if self.viewIfLoaded is not None:
            self.updateCurrencies()
            self.updateExchanges()
            self.tableView.reloadData()

    @objc_method
    def viewDidAppear_(self, animated : bool) -> None:
        '''
        cell = self.multipleChangeCell()
        if cell is None:
            print("WARNING: multipleChanceCell could not be polished! FIXME!")
            return
        parent = gui.ElectrumGui.gui
        b1, enabled = parent.prefs_get_multiple_change()
        utils.uiview_set_enabled(cell, enabled)
        '''
        # do polish here?
        send_super(self,'viewDidAppear:', animated, arg_types=[c_bool])

    @objc_method
    def updateCurrencies(self):
        parent = gui.ElectrumGui.gui
        self.currencies = [_('None')]
        if not parent.daemon.fx: return
        self.currencies = [self.currencies[0],*sorted(parent.daemon.fx.get_currencies(parent.daemon.fx.get_history_config()))]

    @objc_method
    def updateExchanges(self):
        parent = gui.ElectrumGui.gui
        fx = parent.daemon.fx
        self.exchanges = []
        if not fx: return
        b = fx.is_enabled()
        #ex_combo.setEnabled(b)
        if b:
            h = fx.get_history_config()
            c = fx.get_currency()
            self.exchanges = fx.get_exchanges_by_ccy(c, h)
        else:
            self.exchanges = fx.get_exchanges_by_ccy('USD', False)
        #ex_combo.clear()
        #ex_combo.addItems(sorted(exchanges))
        #ex_combo.setCurrentIndex(ex_combo.findText(self.fx.config_exchange()))

        '''
        def update_history_cb():
            if not self.fx: return
            hist_checkbox.setChecked(self.fx.get_history_config())
            hist_checkbox.setEnabled(self.fx.is_enabled())

        def update_fiat_address_cb():
            if not self.fx: return
            fiat_address_checkbox.setChecked(self.fx.get_fiat_address_config())

        '''
    
    ## TableView methods below...   
    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return len(SECTION_TITLES)
    
    @objc_method
    def tableView_titleForHeaderInSection_(self, tv : ObjCInstance, section : int) -> ObjCInstance:
        assert section >= 0 and section < len(SECTION_TITLES)
        return ns_from_py(_(SECTION_TITLES[section]))
    
    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView, section : int) -> int:
        assert section >= 0 and section < len(SECTION_TITLES)
        secName = SECTION_TITLES[section]
        if secName == 'Fees':
            return 2
        elif secName == 'Transactions':
            return 3
        elif secName == 'Appearance':
            return 4
        elif secName == 'Fiat':
            return 4
        return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        assert indexPath.section >= 0 and indexPath.section < len(SECTION_TITLES)
        section,row = indexPath.section, indexPath.row
        secName = SECTION_TITLES[section]
        identifier = "%s_%s_%s"%(str(type(self)) , str(secName), str(row))
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            cell = self.createCellForSection_row_(secName,row)
            self.setupCell_section_row_(cell,secName,row)
        return cell

    @objc_method
    def setupCell_section_row_(self, cell : ObjCInstance, secName_oc : ObjCInstance, row : int) -> None:
        secName = py_from_ns(secName_oc)
        parent = gui.ElectrumGui.gui
        fx = parent.daemon.fx
        cell.tag = 0
        cell.contentView.tag = TAG_CONTENTVIEW
        if secName == 'Fees':
            if row == 0:
                l = cell.viewWithTag_(1)
                tf = cell.viewWithTag_(2)
                l2 = cell.viewWithTag_(3)
                l.text = _('Max static fee')
                tf.placeholder = parent.base_unit()
                l2.text = parent.base_unit() + "/kB"
                tf.delegate = self
                tf.text = str(parent.prefs_get_max_fee_rate())
                tf.addTarget_action_forControlEvents_(self, SEL(b'onMaxStaticFee:'), UIControlEventEditingChanged)
            elif row == 1: # 'edit fees manually', a bool cell
                l = cell.viewWithTag_(1)
                s = cell.viewWithTag_(2)
                s.addTarget_action_forControlEvents_(self, SEL(b'onShowFee:'), UIControlEventValueChanged)
                l.text = _('Edit fees manually')
                s.on =  parent.prefs_get_show_fee()
        elif secName == 'Transactions':
            l = cell.viewWithTag_(1)
            s = cell.viewWithTag_(2)
            if row == 0:
                l.text = _("Use change addresses")
                b, enabled = parent.prefs_get_use_change()
                s.on = b
                utils.uiview_set_enabled(cell, enabled)
                s.addTarget_action_forControlEvents_(self, SEL(b'onUseChange:'), UIControlEventValueChanged)
            elif row == 1:
                cell.contentView.tag = TAG_MULTIPLE_CHANGE_CELL
                l.text = _("Use multiple change addresses")
                b1, enabled = parent.prefs_get_multiple_change()
                s.on = b1
                # for some reason this needs to be called later, not here during setup :/
                utils.call_later(0.500, lambda : utils.uiview_set_enabled(self.multipleChangeCell(), enabled))
                #utils.uiview_set_enabled(self.multipleChangeCell(), enabled)
                s.addTarget_action_forControlEvents_(self, SEL(b'onUseMultiple:'), UIControlEventValueChanged)
            elif row == 2:
                l.text = _("Spend only confirmed coins")
                s.on = parent.prefs_get_confirmed_only()
                s.addTarget_action_forControlEvents_(self, SEL(b'onConfirmedOnly:'), UIControlEventValueChanged)
        elif secName == 'Appearance':
            if row == 0:
                l = cell.viewWithTag_(1)
                s = cell.viewWithTag_(2)
                l.text = _('CashAddr address format')
                s.on = parent.prefs_get_use_cashaddr()
                s.addTarget_action_forControlEvents_(self, SEL(b'onUseCashAddr:'), UIControlEventValueChanged)
            elif row == 1:
                l = cell.viewWithTag_(1)
                p = cell.viewWithTag_(2)
                p = p if p is not None else cell.viewWithTag_(TAG_NZ)
                l.text = _('Zeros after decimal point')
                if p is not None:
                    p.dataSource = self
                    p.delegate = self
                    p.tag = TAG_NZ
                    nr = self.pickerView_numberOfRowsInComponent_(p, 0)
                    nz_prefs = parent.prefs_get_num_zeros()
                    if nz_prefs >= nr:
                        nz_prefs = nr-1
                    p.selectRow_inComponent_animated_(nz_prefs, 0, False)
            elif row == 2:
                l = cell.viewWithTag_(1)
                p = cell.viewWithTag_(2)
                p = p if p is not None else cell.viewWithTag_(TAG_BASE_UNIT)
                l.text = _('Base unit')
                if p is not None:
                    p.dataSource = self
                    p.delegate = self
                    p.tag = TAG_BASE_UNIT
                    try:
                        r,*dummy = [i for i,v in enumerate(UNIT_KEYS) if v == parent.base_unit()]
                        p.selectRow_inComponent_animated_(r, 0, False)
                    except:
                        pass
            elif row == 3:
                l = cell.viewWithTag_(1)
                p = cell.viewWithTag_(2)
                p = p if p is not None else cell.viewWithTag_(TAG_BASE_BLOCK_EXPLORER)
                l.text = _('Online Block Explorer')
                if p is not None:
                    p.dataSource = self
                    p.delegate = self
                    p.tag = TAG_BLOCK_EXPLORER
        elif secName == 'Fiat':
            if row == 0:
                l = cell.viewWithTag_(1)
                p = cell.viewWithTag_(2)
                p = p if p is not None else cell.viewWithTag_(TAG_FIAT_CURRENCY)
                l.text = _('Fiat currency')
                if p is not None:
                    p.dataSource = self
                    p.delegate = self
                    p.tag = TAG_FIAT_CURRENCY
                    if fx.is_enabled():
                        curr = fx.get_currency()
                        currs = py_from_ns(self.currencies)
                        idx = [i for i,v in enumerate(currs) if v == curr]
                        idx = 0 if len(idx) <= 0 else idx[0]
                        if idx > 0: p.selectRow_inComponent_animated_(idx, 0, False)               
            elif row == 1:
                l = cell.viewWithTag_(1)
                s = cell.viewWithTag_(2)
                l.text = _('Show history rates')
                s.on = bool(fx and fx.get_history_config())
                s.addTarget_action_forControlEvents_(self, SEL(b'onFiatHistory:'), UIControlEventValueChanged)
            elif row == 2:
                l = cell.viewWithTag_(1)
                s = cell.viewWithTag_(2)
                l.text = _('Show Fiat balance for addresses')
                s.on = bool(fx and fx.get_fiat_address_config())
                s.addTarget_action_forControlEvents_(self, SEL(b'onFiatBal:'), UIControlEventValueChanged)
            elif row == 3:
                l = cell.viewWithTag_(1)
                p = cell.viewWithTag_(2)
                p = p if p is not None else cell.viewWithTag_(TAG_FIAT_EXCHANGE)
                l.text = _('Source')
                if p is not None:
                    p.dataSource = self
                    p.delegate = self
                    p.tag = TAG_FIAT_EXCHANGE
                    ex = fx.config_exchange() if fx else 'None'
                    exs = self.exchanges
                    idx = [i for i,v in enumerate(exs) if v == ex]
                    idx = 0 if len(idx) <= 0 else idx[0]
                    if len(exs) and idx > 0: p.selectRow_inComponent_animated_(idx, 0, False)               
            
                
    @objc_method
    def createCellForSection_row_(self, secName_oc : ObjCInstance, row : int ) -> ObjCInstance:
        secName = py_from_ns(secName_oc)
        ident = ("%s_%d"%(secName,row))
        cell = None
        
        if ident in ['Fees_1', 'Transactions_0', 'Transactions_1', 'Transactions_2', 'Appearance_0', 'Fiat_1', 'Fiat_2']:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("BoolCell",self.tableView,None)
            assert objs is not None and len(objs)
            cell = objs[0] 
        elif ident in ['Fees_0']:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("TFCell",self.tableView,None)
            assert objs is not None and len(objs)
            cell = objs[0]
        elif ident in ['Appearance_1', 'Appearance_2', 'Appearance_3', 'Fiat_0', 'Fiat_3']:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("PickerCell",self.tableView,None)
            assert objs is not None and len(objs)
            cell = objs[0]

        assert cell is not None
        return cell

    ### TextField delegate crap ###
    @objc_method
    def textFieldShouldReturn_(self, tf : ObjCInstance) -> bool:
        tf.resignFirstResponder()
        self.onMaxStaticFee_(tf)
        return True
    
    
    ## UIPickerViewDataSource delegate ##
    @objc_method
    def numberOfComponentsInPickerView_(self, p : ObjCInstance) -> int:
        return 1
    @objc_method
    def  pickerView_numberOfRowsInComponent_(self, p : ObjCInstance, component : int) -> int:
        assert component == 0
        parent = gui.ElectrumGui.gui
        if p.tag == TAG_BASE_UNIT: return len(UNIT_KEYS)
        elif p.tag == TAG_NZ: return min(parent.get_decimal_point(), 8) + 1
        elif p.tag == TAG_BLOCK_EXPLORER: return len(web.BE_sorted_list())
        elif p.tag == TAG_FIAT_CURRENCY: return len(self.currencies)
        elif p.tag == TAG_FIAT_EXCHANGE: return len(self.exchanges)
        else: raise ValueError('Unknown pickerView tag: {}'.format(int(p.tag)))
        return 0
    @objc_method
    def pickerView_didSelectRow_inComponent_(self, p : ObjCInstance, row : int, component : int) -> None:
        parent = gui.ElectrumGui.gui
        if p.tag == TAG_BASE_UNIT:
            dec = UNITS.get(UNIT_KEYS[row],None)
            if dec is None:
                raise Exception('Unknown base unit')
            parent.prefs_set_decimal_point(dec)
        elif p.tag == TAG_NZ:
            parent.prefs_set_num_zeros(row)
        elif p.tag == TAG_BLOCK_EXPLORER:
            be = web.BE_sorted_list()[row]
            parent.config.set_key('block_explorer', be, True)
        elif p.tag == TAG_FIAT_CURRENCY:
            is_en = bool(row)
            ccy = self.currencies[row] if is_en else None
            parent.daemon.fx.set_enabled(is_en)
            need_refresh = ccy != parent.daemon.fx.ccy
            if is_en and ccy is not None and ccy != parent.daemon.fx.ccy:
                parent.daemon.fx.set_currency(ccy)
            if need_refresh: parent.refresh_all()
        elif p.tag == TAG_FIAT_EXCHANGE:
            fx = parent.daemon.fx
            exchange = self.exchanges[row] if row < len(self.exchanges) else None
            if fx and fx.is_enabled() and exchange and exchange != fx.exchange.name():
                fx.set_exchange(exchange)
    
            
    @objc_method
    def  pickerView_viewForRow_forComponent_reusingView_(self, p : ObjCInstance, row : int, component : int, view : ObjCInstance) -> ObjCInstance:
        def getTitle(p : ObjCInstance, row : int) -> str:
            if p.tag == TAG_BASE_UNIT: return str(UNIT_KEYS[row])
            elif p.tag == TAG_NZ: return str('%d'%(row))
            elif p.tag == TAG_BLOCK_EXPLORER: return str(web.BE_sorted_list()[row])
            elif p.tag == TAG_FIAT_CURRENCY: return str(self.currencies[row])
            elif p.tag == TAG_FIAT_EXCHANGE: return str(self.exchanges[row])
            else: raise ValueError('Unknown pickerView tag: {}'.format(int(p.tag)))
            return '*Error*' # not reached
        assert component == 0
        tit = getTitle(p, row)
        l = view if view is not None else UILabel.new().autorelease()
        l.text = tit
        l.textColor = UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,0.5,1.0)
        l.minimumScaleFactor = 0.5
        l.adjustsFontSizeToFitWidth = True
        return l
        
    
    ### ACTION HANDLERS -- basically calls back into gui object ###
    @objc_method
    def onShowFee_(self, but : ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        parent.prefs_set_show_fee(but.isOn())
    @objc_method
    def onMaxStaticFee_(self, tf : ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        print("On Max Static Fee: %s"%str(tf.text))
        val = parent.prefs_set_max_fee_rate(tf.text)
        if str(val) != str(tf.text) and not tf.isFirstResponder:
            tf.text = str(val)
    @objc_method
    def onConfirmedOnly_(self, s : ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        parent.prefs_set_confirmed_only(bool(s.isOn()))
    @objc_method
    def onUseChange_(self, s: ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        parent.prefs_set_use_change(bool(s.isOn()))
        b1, enabled = parent.prefs_get_multiple_change()
        utils.uiview_set_enabled(self.multipleChangeCell(), enabled)
    @objc_method
    def onUseMultiple_(self, s: ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        parent.prefs_set_multiple_change(bool(s.isOn()))
    @objc_method
    def onUseCashAddr_(self, s: ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        parent.toggle_cashaddr(bool(s.isOn()))
    @objc_method
    def onFiatHistory_(self, s: ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        fx = parent.daemon.fx
        if not fx: return
        fx.set_history_config(s.isOn())
        self.updateExchanges()
        p = self.tableView.viewWithTag_(TAG_FIAT_EXCHANGE)
        if p is not None: p.reloadData()
        parent.historyVC.needUpdate()
        if fx.is_enabled() and s.isOn():
            # reset timeout to get historical rates
            fx.timeout = 0
    @objc_method
    def onFiatBal_(self, s: ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        fx = parent.daemon.fx
        if not fx: return
        fx.set_fiat_address_config(s.isOn())
        parent.addressesVC.needUpdate()