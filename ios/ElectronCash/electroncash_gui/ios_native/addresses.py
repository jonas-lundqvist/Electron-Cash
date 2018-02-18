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

class AddressDetail(UIViewController):
    addrInfo = objc_property() # an NSArray of stuff to display
    
    @objc_method
    def initWithAddrInfo_(self, addrInfo):
        self = ObjCInstance(send_super(self, 'init'))
        self.addrInfo = addrInfo
        self.title = "Address Information"
        return self
    
    @objc_method
    def dealloc(self) -> None:
        #print("AddressDetail dealloc")
        self.addrInfo = None
        self.title = None
        self.view = None
        send_super(self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        self.view = UIView.alloc().init().autorelease()
        lbl = UILabel.alloc().init().autorelease()
        lbl.text = "Address Detail: " + str(self.addrInfo[0])
        lbl.adjustsFontSizeForWidth = True
        lbl.numberOfLines = 2
        w = UIScreen.mainScreen.bounds.size.width
        rect = CGRectMake(0,100,w,80)
        lbl.frame = rect
        self.view.addSubview_(lbl)

 
# Addresses Tab -- shows addresses, etc
class AddressesTableVC(UITableViewController):
    needsRefresh = objc_property()

    @objc_method
    def initWithStyle_(self, style : int):
        self = ObjCInstance(send_super(self, 'initWithStyle:', style, argtypes=[c_int]))
        self.needsRefresh = False
                
        self.refreshControl = UIRefreshControl.alloc().init().autorelease()
        self.refreshControl.addTarget_action_forControlEvents_(self,SEL('needUpdate'), UIControlEventValueChanged)

        heartbeat.Add(self, 'doRefreshIfNeeded')

        return self

    @objc_method
    def dealloc(self) -> None:
        heartbeat.Remove(self, 'doRefreshIfNeeded')
        self.needsRefresh = None
        send_super(self, 'dealloc')

    @objc_method
    def numberOfSectionsInTableView_(self, tableView) -> int:
        return 3
    
    @objc_method
    def tableView_titleForHeaderInSection_(self, tv : ObjCInstance,section : int) -> ObjCInstance:
        return {
            0 : "Addresses With Funds",
            1 : "Used, Emptied Addresses",
            2 : "Unused Addresses"
        }.get(section, 2)

    @objc_method
    def tableView_numberOfRowsInSection_(self, tableView : ObjCInstance, section : int) -> int:
        try:
            parent = gui.ElectrumGui.gui
            return 4 if section < 2 else 16
        except:
            print("Error, no addresses")
            return 0

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tableView, indexPath):
        identifier = "%s_%s"%(str(type(self)) , str(indexPath.section))
        cell = tableView.dequeueReusableCellWithIdentifier_(identifier)
        if cell is None:
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
        try:
            parent = gui.ElectrumGui.gui
            title = utils.nsattributedstring_from_html('<font face="system font,arial,helvetica,verdana"><b>A Title %s</b></font>'%str(indexPath.section*4+indexPath.row))
            detail = utils.nsattributedstring_from_html('<font face="system font,arial,helvetica,verdana" color="#333344" size="-1">Some detail for %s</font>'%str(indexPath.section*4+indexPath.row))
            pstyle = NSMutableParagraphStyle.alloc().init().autorelease()
            pstyle.lineBreakMode = NSLineBreakByTruncatingTail
            title.addAttribute_value_range_(NSParagraphStyleAttributeName, pstyle, NSRange(0,title.length()))
            detail.addAttribute_value_range_(NSParagraphStyleAttributeName, pstyle, NSRange(0,detail.length()))
            cell.imageView.image = None
            cell.textLabel.text = None
            cell.textLabel.adjustsFontSizeToFitWidth = False
            cell.textLabel.lineBreakMode = NSLineBreakByTruncatingTail
            cell.textLabel.numberOfLines = 1
            cell.textLabel.attributedText = title
            cell.textLabel.updateConstraintsIfNeeded()
            cell.detailTextLabel.text = None
            cell.detailTextLabel.adjustsFontSizeToFitWidth = False
            cell.detailTextLabel.lineBreakMode = NSLineBreakByTruncatingTail
            cell.detailTextLabel.numberOfLines = 1
            cell.detailTextLabel.attributedText = detail
            cell.detailTextLabel.updateConstraintsIfNeeded()
            cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator
        except Exception as e:
            print("exception in addresses tableView_cellForRowAtIndexPath_: %s"%str(e))
            cell.textLabel.attributedText = None
            cell.textLabel.text = "*Error*"
            cell.detailTextLabel.attributedText = None
            cell.detailTextLabel.text = None
            cell.accessoryType = None
        return cell
    
    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath):
        #print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        #print("DID SELECT ROW CALLED FOR SECTION %s, ROW %s"%(str(indexPath.section),str(indexPath.row)))
        parent = gui.ElectrumGui.gui
        parent.addressesNav.pushViewController_animated_(AddressDetail.alloc().initWithAddrInfo_(['Some Info for addr %d'%(indexPath.section*4+indexPath.row)]).autorelease(), True)
 
    
    @objc_method
    def updateAddressesFromWallet(self):
        parent = gui.ElectrumGui.gui
        wallet = parent.wallet


    @objc_method
    def refresh(self):
        self.updateAddressesFromWallet()
        try:
            self.refreshControl.endRefreshing()
        except:
            pass
        self.tableView.reloadData()
        self.needsRefresh = False

    @objc_method
    def needUpdate(self):
        self.needsRefresh = True

    # This method runs in the main thread as it's enqueue using our hacky "Heartbeat" mechanism/workaround for iOS
    @objc_method
    def doRefreshIfNeeded(self):
        if self.needsRefresh:
            self.refresh()

    @objc_method
    def showRefreshControl(self):
        if self.refreshControl is not None and not self.refreshControl.isRefreshing():
            # the below starts up the table view in the "refreshing" state..
            self.refreshControl.beginRefreshing()
            self.tableView.setContentOffset_animated_(CGPointMake(0, self.tableView.contentOffset.y-self.refreshControl.frame.size.height), True)
