from . import utils
from . import gui
from . import heartbeat
from electroncash.util import timestamp_to_datetime
from electroncash.i18n import _, language
import time
import html
from .uikit_bindings import *


SECTION_TITLES = [ 'Fees', 'Transactions', 'Appearance', 'Fiat',
                  #'Identity'
                  ]

class PrefsVC(UITableViewController):
    
    closeButton = objc_property() # caller sets this
    
    multipleChangeCell = objc_property() # so we may disable/enable it
    
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
        self.multipleChangeCell = None
        send_super(self, 'dealloc')

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
        #elif secName == 'Appearance':
        #    return 4
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
        if secName == 'Fees':
            if row == 0:
                l = cell.viewWithTag_(1)
                tf = cell.viewWithTag_(2)
                l2 = cell.viewWithTag_(3)
                l.text = _('Max static fee')
                tf.placeholder = parent.base_unit()
                l2.text = parent.base_unit() + " / kB"
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
                self.multipleChangeCell = cell
                l.text = _("Use multiple change addresses")
                b1, enabled = parent.prefs_get_multiple_change()
                s.on = b1
                # for some reason this needs to be called later, not here during setup :/
                utils.call_later(0.100, lambda : utils.uiview_set_enabled(self.multipleChangeCell, enabled))
                s.addTarget_action_forControlEvents_(self, SEL(b'onUseMultiple:'), UIControlEventValueChanged)
            elif row == 2:
                l.text = _("Spend only confirmed coins")
                s.on = parent.prefs_get_confirmed_only()
                s.addTarget_action_forControlEvents_(self, SEL(b'onConfirmedOnly:'), UIControlEventValueChanged)                
                
    @objc_method
    def createCellForSection_row_(self, secName_oc : ObjCInstance, row : int ) -> ObjCInstance:
        secName = py_from_ns(secName_oc)
        ident = ("%s_%d"%(secName,row))
        cell = None
        
        if ident in ['Fees_1', 'Transactions_0', 'Transactions_1', 'Transactions_2',]:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("BoolCell",self.tableView,None)
            assert objs is not None and len(objs)
            cell = objs[0] 
        elif ident in ['Fees_0']:
            objs = NSBundle.mainBundle.loadNibNamed_owner_options_("TFCell",self.tableView,None)
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
        if self.multipleChangeCell is not None:
            b1, enabled = parent.prefs_get_multiple_change()
            utils.uiview_set_enabled(self.multipleChangeCell, enabled)
    @objc_method
    def onUseMultiple_(self, s: ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui
        parent.prefs_set_multiple_change(bool(s.isOn()))
