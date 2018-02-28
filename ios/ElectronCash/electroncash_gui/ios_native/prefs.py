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

UNITS = { 'BCH': 8, 'mBCH': 5, 'bits' : 2}
UNIT_KEYS = list(UNITS.keys())
UNIT_KEYS.sort(key=lambda x: UNITS[x],reverse=True)


class PrefsVC(UITableViewController):
    
    closeButton = objc_property() # caller sets this
        
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(self, 'initWithStyle:', UITableViewStyleGrouped, argtypes=[c_int]))
        self.title = _("Preferences")
        self.closeButton = None
        return self
    
    @objc_method
    def initWithStyle_(self, style : int) -> ObjCInstance:
        print("WARNING: PrefsVC doesn't support the initWithStyle: method -- use plain old 'init' instead!")
        assert style == UITableViewStyleGrouped
        return self.init()
        
    @objc_method
    def dealloc(self) -> None:
        self.closeButton = None
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
            self.tableView.reloadData()

    @objc_method
    def viewDidAppear_(self, animated : bool) -> None:
        cell = self.multipleChangeCell()
        if cell is None:
            print("WARNING: multipleChanceCell could not be polished! FIXME!")
            return
        parent = gui.ElectrumGui.gui
        b1, enabled = parent.prefs_get_multiple_change()
        utils.uiview_set_enabled(cell, enabled)
    
        send_super(self,'viewDidAppear:', animated, arg_types=[c_bool])

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
        #elif secName == 'Fiat':
        #    return 4
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
                # we opted to do it in viewDidAppear: method since that's safer than this call_later callback mechanism which sometimes crashes
                #utils.call_later(0.500, lambda : utils.uiview_set_enabled(self.multipleChangeCell(), enabled))
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
                l.text = _('Online Block Explorer')
                if p is not None:
                    p.dataSource = self
                    p.delegate = self
                    p.tag = TAG_BLOCK_EXPLORER
            
                
    @objc_method
    def createCellForSection_row_(self, secName_oc : ObjCInstance, row : int ) -> ObjCInstance:
        secName = py_from_ns(secName_oc)
        ident = ("%s_%d"%(secName,row))
        cell = None
        
        if ident in ['Fees_1', 'Transactions_0', 'Transactions_1', 'Transactions_2', 'Appearance_0']:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("BoolCell",self.tableView,None)
            assert objs is not None and len(objs)
            cell = objs[0] 
        elif ident in ['Fees_0']:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("TFCell",self.tableView,None)
            assert objs is not None and len(objs)
            cell = objs[0]
        elif ident in ['Appearance_1', 'Appearance_2', 'Appearance_3']:
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
            pass
        
            
    @objc_method
    def  pickerView_titleForRow_forComponent_(self, p : ObjCInstance, row : int, component : int) -> ObjCInstance:
        assert component == 0
        if p.tag == TAG_BASE_UNIT: return ns_from_py(UNIT_KEYS[row])
        elif p.tag == TAG_NZ: return ns_from_py(str('%d'%(row)))
        elif p.tag == TAG_BLOCK_EXPLORER: return ns_from_py(web.BE_sorted_list()[row])
        else: raise ValueError('Unknown pickerView tag: {}'.format(int(p.tag)))
        return ns_from_py('Error') # not reached

    @objc_method
    def  pickerView_attributedTitleForRow_forComponent_(self, p : ObjCInstance, row : int, component : int) -> ObjCInstance:
        tit = py_from_ns(self.pickerView_titleForRow_forComponent_(p, row, component))
        return utils.nsattributedstring_from_html('<font size="3" color="#000066" face="Helvetica">{}</font>'.format(tit))
    
#    @objc_method
#    def pickerView_rowHeightForComponent_(self, p: ObjCInstance, component : int) -> float:
#        return 15.0
    
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