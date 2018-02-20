from electroncash.i18n import _, language
from . import utils
from . import gui
from .uikit_bindings import *

# returns the view itself, plus the copy button and the qrcode button, plus the (sometimes nil!!) UITextField for the editable description
#  the copy and the qrcode buttons are so that caller may attach event handing to them
def create_transaction_detail_view(entry) -> (ObjCInstance, ObjCInstance, ObjCInstance, ObjCInstance):
    dummy, tx_hash, status_str, label, v_str, balance_str, date, conf, status, value, img, *dummy2 = entry
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    base_unit = parent.base_unit()
    format_amount = parent.format_amount

    tx = wallet.transactions.get(tx_hash)
    tx_hash, status_, label_, can_broadcast, amount, fee, height, conf, timestamp, exp_n = wallet.get_tx_info(tx)
    size = tx.estimated_size()
    # todo: broadcast button based on 'can_broadcast'
    can_sign = not tx.is_complete() and wallet.can_sign(tx) #and (wallet.can_sign(tx) # or bool(self.main_window.tx_external_keypairs))
    # todo: something akin to this: self.sign_button.setEnabled(can_sign)

    viewsV1 = []
    viewsV2 = []
    viewsH1 = []

    v = UILabel.new().autorelease()
    v.text = _("Transaction ID:")
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisVertical)
    viewsV1.append(v)
    v = UILabel.new().autorelease()
    v.text = tx_hash if tx_hash is not None and tx_hash != "None" else _('Unknown')
    v.backgroundColor = UIColor.colorWithWhite_alpha_(0.0,0.075)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultLow, UILayoutConstraintAxisHorizontal)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisVertical)
    v.adjustsFontSizeToFitWidth = True
    v.minimumScaleFactor = 0.25
    v.numberOfLines = 0
    v.lineBreakMode = NSLineBreakByTruncatingTail
    viewsH1.append(v)
    v = UIButton.buttonWithType_(UIButtonTypeCustom)
    but1 = v
    v.setImage_forState_(utils.uiimage_get("copy.png"), UIControlStateNormal)
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisVertical)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultLow-1, UILayoutConstraintAxisVertical)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultLow-1, UILayoutConstraintAxisHorizontal)
    viewsH1.append(v)
    v = UIButton.buttonWithType_(UIButtonTypeCustom)
    but2 = v
    v.setImage_forState_(utils.uiimage_get("qrcode.png"), UIControlStateNormal)
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisVertical)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultLow-1, UILayoutConstraintAxisVertical)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultLow-1, UILayoutConstraintAxisHorizontal)
    viewsH1.append(v)

    sv = UIStackView.alloc().initWithArrangedSubviews_(viewsH1).autorelease()
    sv.axis = UILayoutConstraintAxisHorizontal
    sv.layoutMargins = UIEdgeInsetsMake(0,10,0,-5)
    sv.spacing = 3.0
    sv.layoutMarginsRelativeArrangement = True

    viewsV1.append(sv)
    viewsH1 = []

    descriptionTF = None
    
    if tx_hash is not None and len(tx_hash): # always do this so they can edit the description to add a label to an empty tx
        v = UILabel.new().autorelease()
        v.text = _("Description:") + "  "
        v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
        v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
        viewsV1.append(v)

        v = UITextField.new().autorelease() 
        v.text = label
        if amount < 0:
            v.backgroundColor = UIColor.colorWithRed_green_blue_alpha_(1.0,0.2,0.2,0.040)
        else:
            v.backgroundColor = UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,1.0,0.040)
        v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
        v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisVertical)
        v.adjustsFontSizeToFitWidth = True
        v.minimumFontSize = 8.0
        v.borderStyle = UITextBorderStyleLine
        v.clearButtonMode = UITextFieldViewModeWhileEditing
        descriptionTF = v
        
        
        sv = UIStackView.alloc().initWithArrangedSubviews_([v]).autorelease()
        sv.layoutMargins = UIEdgeInsetsMake(0,10,0,-5)
        sv.axis = UILayoutConstraintAxisHorizontal
        sv.spacing = 5.0
        sv.layoutMarginsRelativeArrangement = True
        viewsV1.append(sv)
 
    v = UILabel.new().autorelease()
    v.text = _("Status:") + "  "
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
    viewsH1.append(v)
    
    v = UIImageView.alloc().initWithImage_(img).autorelease()
    v.autoresizingMask = UIViewAutoresizingNone
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultLow, UILayoutConstraintAxisHorizontal)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultLow, UILayoutConstraintAxisHorizontal)
    viewsH1.append(v)

    v = UILabel.new().autorelease()
    ff = status_str
    try:
        if int(conf) > 0:
           ff = "%s %s"%(conf, _('confirmations'))
    except:
        pass        
    v.text = _(ff)
    viewsH1.append(v)
    
    sv = UIStackView.alloc().initWithArrangedSubviews_(viewsH1).autorelease()
    viewsH1 = []
    sv.axis = UILayoutConstraintAxisHorizontal
    sv.spacing = 5.0
    viewsV1.append(sv)

    if timestamp or exp_n:
        v = UILabel.new().autorelease()
        if timestamp:
            v.text = _("Date: {}").format("  ")
        elif exp_n:
            v.text = _("Expected confirmation time") + ':  '
        v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
        v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
        viewsH1.append(v)

        v = UILabel.new().autorelease()
        if timestamp:
            v.text = date
        elif exp_n:
            txt = '%d blocks'%(exp_n) if exp_n > 0 else _('unknown (low fee)')
            v.text = _('Expected confirmation time') + ': ' + txt
        viewsH1.append(v)
        
        sv = UIStackView.alloc().initWithArrangedSubviews_(viewsH1).autorelease()
        viewsH1 = []
        sv.axis = UILayoutConstraintAxisHorizontal
        sv.spacing = 5.0
        viewsV1.append(sv)
        
    v = UILabel.new().autorelease()
    if amount is None:
        amount_str = _("Transaction unrelated to your wallet")
    elif amount > 0:
        amount_str = _("Amount received:") + ' %s'% format_amount(amount) + ' ' + base_unit
    else:
        amount_str = _("Amount sent:") + ' %s'% format_amount(-amount) + ' ' + base_unit
    v.text = amount_str
    v.adjustsFontSizeToFitWidth = True
    v.minimumScaleFactor = 0.25
    v.numberOfLines = 0
    v.lineBreakMode = NSLineBreakByTruncatingTail
    viewsV1.append(v)

    size_str = _("Size:") + ' %d bytes'% size
    v = UILabel.new().autorelease()
    v.text = size_str
    v.adjustsFontSizeToFitWidth = True
    v.minimumScaleFactor = 0.25
    v.numberOfLines = 0
    v.lineBreakMode = NSLineBreakByTruncatingTail
    viewsV1.append(v)
    
    fee_str = _("Fee") + ': %s'% (format_amount(fee) + ' ' + base_unit if fee is not None else _('unknown'))
    if fee is not None:
        fee_str += '  ( %s ) '%  parent.format_fee_rate(fee/size*1000)
    v = UILabel.new().autorelease()
    v.text = fee_str
    v.adjustsFontSizeToFitWidth = True
    v.minimumScaleFactor = 0.25
    v.numberOfLines = 0
    v.lineBreakMode = NSLineBreakByTruncatingTail
    viewsV1.append(v)


    # bottom spacer view -- why?!?!        
    v = UIView.new().autorelease()
    v.autoresizingMask = UIViewAutoresizingFlexibleHeight
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisHorizontal)
    v.setContentHuggingPriority_forAxis_(UILayoutPriorityDefaultHigh, UILayoutConstraintAxisVertical)
    v.setContentCompressionResistancePriority_forAxis_(UILayoutPriorityDefaultLow, UILayoutConstraintAxisVertical)
    viewsV1.append(v)
    
    sv = UIStackView.alloc().initWithArrangedSubviews_(viewsV1).autorelease()
    sv.axis = UILayoutConstraintAxisVertical
    sv.spacing = 10.0
    #sv.distribution = UIStackViewDistributionFill
    #sv.alignment = UIStackViewAlignmentFill
    sv.layoutMarginsRelativeArrangement = True
    #view = UIView.new().autorelease()
    view = UIScrollView.new().autorelease()
    sv.layoutMargins = UIEdgeInsetsMake(0,15,0,10) # top,left,bottom,right
    sv.autoresizingMask = UIViewAutoresizingFlexibleHeight|UIViewAutoresizingFlexibleWidth
    view.addSubview(sv)
    sv.layoutIfNeeded()
    view.contentSize = sv.systemLayoutSizeFittingSize_(CGSizeMake(UIScreen.mainScreen.bounds.size.width, 0))
    return (view, but1, but2, descriptionTF)
