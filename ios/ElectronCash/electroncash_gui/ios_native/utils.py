#!/usr/bin/env python3
#
# Electron Cash - lightweight Bitcoin Cash client
# Copyright (C) 2012 thomasv@gitorious
# Copyright (C) 2018 calin.culianu@gmail.com
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import sys
import os
from inspect import signature
from .uikit_bindings import *
from .custom_objc import *

bundle_identifier = NSBundle.mainBundle.bundleIdentifier
bundle_domain = '.'.join(bundle_identifier.split('.')[0:-1])
bundle_short_name = bundle_domain + ".ElectronCash"

def is_2x_screen() -> bool:
    return True if UIScreen.mainScreen.scale > 1.0 else False

def get_fn_and_ext(fileName: str) -> tuple:
    *p1, ext = fileName.split('.')
    fn=''
    if len(p1) is 0:
        fn = ext
        ext = None
    else:
        fn = '.'.join(p1) 
    return (fn,ext)

def uiview_set_enabled(view : ObjCInstance, b : bool) -> None:
    if view is None: return
    view.userInteractionEnabled = b
    view.alpha = float(1.0 if b else 0.3)

# NB: This isn't normally called since you need to specify the full pathname of the resource you want, instead
#     if you need images, call uiimage_get, etc.  This does NOT search recursively, since NSBundle sucks.
def get_bundle_resource_path(fileName: str, directory: str = None) -> str:
    fn,ext = get_fn_and_ext(fileName)
    if directory is None:
        return NSBundle.mainBundle.pathForResource_ofType_(fn, ext)
    return NSBundle.mainBundle.pathForResource_ofType_inDirectory_(fn, ext, directory)

def nsattributedstring_from_html(html : str) -> ObjCInstance:
    data = ns_from_py(html.encode('utf-8'))
    return NSMutableAttributedString.alloc().initWithHTML_documentAttributes_(data,None).autorelease()

callables_tmp = {}
completion_tmp = None
alerts_helpful_glue = None
    

def show_alert(vc : ObjCInstance, # the viewcontroller to present the alert view in
               title : str, # the alert title
               message : str, # the alert message
               # actions is a list of lists: each element has:  Button names, plus optional callback spec
               # each element of list is [ 'ActionTitle', callable, arg1, arg2... ] for optional callbacks
               actions: list = [ ['Ok'] ],  # default has no callbacks and shows Ok button
               cancel: str = None, # name of the button you want to designate as 'Cancel' (ends up being first)
               destructive: str = None, # name of the button you want to designate as destructive (ends up being red)
               alertStyle: int = UIAlertControllerStyleAlert,
               completion: callable = None, # optional completion function that gets called when alert is presented
               animated: bool = True # whether or not to animate the alert
               ) -> None:
    assert NSThread.currentThread.isMainThread
    global alerts_helpful_glue
    global callables_tmp
    global completion_tmp
    if alerts_helpful_glue is not None:
        print("WARNING / FIXME: private HelpfulGlue instance was not None -- possible leak?")
    alerts_helpful_glue = HelpfulGlue.new()
    alert = UIAlertController.alertControllerWithTitle_message_preferredStyle_(title, message, alertStyle)
    callables_tmp = {}
    completion_tmp = None
    if type(actions) is dict:
        acts = []
        for k in actions.keys():
            if actions[k] is not None:
                acts.append([k,*actions[k]])
            else:
                acts.appens([k])
        actions = acts
    ct=0
    for i,arr in enumerate(actions):
        has_callable = False
        if type(arr) is list or type(arr) is tuple:
            actTit = arr[0]
            fun_args = arr[1:]
            has_callable = True
        else:
            actTit = arr
        style = UIAlertActionStyleCancel if actTit == cancel else UIAlertActionStyleDefault
        style = UIAlertActionStyleDestructive if actTit == destructive else style
        act = alerts_helpful_glue.actionWithTitle_style_python_(actTit,style,'''
import electroncash_gui.ios_native.utils as u
from electroncash_gui.ios_native.custom_objc import *

if u.callables_tmp.get(action_ptr):
    arr = u.callables_tmp[action_ptr]
    fun = arr[0]
    fun(*arr[1:])
u.callables_tmp = {}
if u.alerts_helpful_glue is not None:
    u.alerts_helpful_glue.autorelease()
    u.alerts_helpful_glue = None
''')
        if has_callable:
            callables_tmp[act.ptr.value] = fun_args
        alert.addAction_(act)
        ct+=1
    if completion is not None:
        completion_tmp = completion
        HelpfulGlue.viewController_presentModalViewController_animated_python_(vc,alert,animated,'''
import electroncash_gui.ios_native.utils as u
if u.completion_tmp is not None:
    u.completion_tmp()
u.completion_tmp = None
''')
    else:
        HelpfulGlue.viewController_presentModalViewController_animated_python_(vc,alert,animated,None)
    if not ct:
        # weird.. they didn't supply any buttons to the alert -- perhaps they want some "please wait.." style alert..?
        # clean up the unneeded instance...
        alerts_helpful_glue.autorelease()
        alerts_helful_glue = None
        #print("Removed unneded private HelpfulGlue...")

# Useful for doing a "Please wait..." style screen that takes itself offscreen automatically after a delay
# (may end up using this for some info alerts.. not sure yet)
def show_timed_alert(vc : ObjCInstance, title : str, message : str,
                     timeout : float, alertStyle : int = UIAlertControllerStyleAlert, animated : bool = True) -> None:
    assert NSThread.currentThread.isMainThread
    def completionFunc(vc,animated,timeout):
        #print("Completion on %s %s..."%(str(vc.ptr.value),str(animated)))
        def dismisser(vc,animated):
            #print("Dismisser on %s %s..."%(str(vc.ptr.value),str(animated)))
            HelpfulGlue.viewController_dismissModalViewControllerAnimated_python_(vc,animated,None)
        call_later(timeout, dismisser, vc, animated)
    show_alert(vc=vc, title=title, message=message, actions=[], alertStyle=alertStyle, completion=lambda: completionFunc(vc,animated,timeout))


def do_in_main_thread(func : callable, *args) -> None:
    if NSThread.currentThread.isMainThread:
        func(*args)
    else:
        call_later(0.001, func, *args)

calllater_blks = {}
def call_later(timeout : float, func : callable, *args) -> None:
    global calllater_blks
    def OnTimer(t_in : objc_id) -> None:
        global calllater_blks
        t = ObjCInstance(t_in)
#        print("OnTimer called with t=%d, calling func"%(t.ptr.value))
        func(*args)
        if calllater_blks.get(t.ptr.value,None) is not None:
            del calllater_blks[t.ptr.value]
#            print("Deleted block from table")
#        else:
#            print("Could not find block in table!")
    blk = Block(OnTimer)
    timer = NSTimer.timerWithTimeInterval_repeats_block_(timeout, False, blk)
    calllater_blks[timer.ptr.value] = blk # keep it around
    NSRunLoop.mainRunLoop().addTimer_forMode_(timer, NSDefaultRunLoopMode)
    
###
### Modal picker stuff
###
pickerCallables = {}
class UTILSModalPickerHelper(UIViewController):
    
    items = objc_property()
    lastSelection = objc_property()
    needsDismiss = objc_property()
 
    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(self,'init'))
        self.items = None
        self.lastSelection = 0
        self.needsDismiss = False
        return self
    
    @objc_method
    def dealloc(self) -> None:
        self.finished()
        self.view = None
        self.needsDismiss = None
#        print("UTILSModalPickerHelper dealloc")
        send_super(self, 'dealloc')
    
    @objc_method
    def numberOfComponentsInPickerView_(self, p : ObjCInstance) -> int:
        return 1
    @objc_method
    def  pickerView_numberOfRowsInComponent_(self, p : ObjCInstance, component : int) -> int:
        assert component == 0
        return len(self.items)    
    @objc_method
    def pickerView_didSelectRow_inComponent_(self, p : ObjCInstance, row : int, component : int) -> None:
        assert component == 0 and row < len(self.items)
        self.lastSelection = row
                
    @objc_method
    def  pickerView_titleForRow_forComponent_(self, p : ObjCInstance, row : int, component : int) -> ObjCInstance:
        assert component == 0 and row < len(self.items)
        return ns_from_py(self.items[row])
    
    @objc_method
    def onOk_(self, but : ObjCInstance) -> None:
#        print ("Ok pushed")
        global pickerCallables
        cb = pickerCallables.get(self.ptr.value, None) 
        if cb is not None:
            sig = signature(cb)
            params = sig.parameters
            if len(params) > 0:
                cb(int(self.lastSelection))
            else:
                cb()
        self.finished()
        self.autorelease()
         
    @objc_method
    def onCancel_(self, but : ObjCInstance) -> None:
#        print ("Cancel pushed")        
        self.finished()
        self.autorelease()

    @objc_method
    def finished(self) -> None:
        global pickerCallables
        if pickerCallables.get(self.ptr.value, None) is not None: del pickerCallables[self.ptr.value]  
        if self.viewIfLoaded is not None and self.needsDismiss:
            HelpfulGlue.viewController_dismissModalViewControllerAnimated_python_(self,True,None)
        self.items = None
        self.lastSelection = None
        self.needsDismiss = False

def present_modal_picker(parentVC : ObjCInstance,
                         items : list,
                         selectedIndex : int = 0,
                         okCallback : callable = None,
                         okButtonTitle : str = "OK",
                         cancelButtonTitle : str = "Cancel") -> ObjCInstance:
    assert parentVC is not None and items is not None and len(items)
    helper = UTILSModalPickerHelper.new()
    objs = NSBundle.mainBundle.loadNibNamed_owner_options_("ModalPickerView",helper,None)
    if objs is None or not len(objs):
        raise Exception("Could not load ModalPickerView nib!")
    mpv = objs[0]
    p = mpv.viewWithTag_(200)
    okBut = mpv.viewWithTag_(1)
    okLbl = mpv.viewWithTag_(11)
    cancelBut = mpv.viewWithTag_(2)
    cancelLbl = mpv.viewWithTag_(22)
    assert p and okBut and cancelBut
    if okButtonTitle is not None and okLbl is not None: okLbl.text = okButtonTitle
    if cancelButtonTitle is not None and cancelLbl is not None: cancelLbl.text = cancelButtonTitle
    helper.view = mpv
    helper.items = items
    okBut.addTarget_action_forControlEvents_(helper, SEL(b'onOk:'), UIControlEventTouchUpInside)
    cancelBut.addTarget_action_forControlEvents_(helper, SEL(b'onCancel:'), UIControlEventTouchUpInside)
    p.delegate = helper
    p.dataSource = helper
    if okCallback is not None: pickerCallables[helper.ptr.value] = okCallback
    if selectedIndex > 0 and selectedIndex < len(items):
        p.selectRow_inComponent_animated_(selectedIndex, 0, False)
        helper.lastSelection = selectedIndex
    helper.modalPresentationStyle = UIModalPresentationOverCurrentContext
    helper.disablesAutomaticKeyboardDismissal = False
    HelpfulGlue.viewController_presentModalViewController_animated_python_(parentVC,helper,True,None)
    helper.needsDismiss = True
    return helper


cw_notif_blocks = {} # need to keep the Block instances around else objc crashes.. they get reaped in dealloc below..
class MyNotif(CWStatusBarNotification):
    @objc_method
    def dealloc(self) -> None:
        global cw_notif_blocks
        if cw_notif_blocks.get(self.ptr.value, None) is not None:
            del cw_notif_blocks[self.ptr.value]
            #print("deleted block")
        #print('%ld MyNotif dealloc...'%int(self.ptr.value))
        send_super(self, 'dealloc')
def show_notification(message : str,
                      duration : float = 2.0, # the duration is in seconds
                      color : tuple = None, # color needs to have r,g,b,a components -- length 4!
                      style : int = CWNotificationStyleStatusBarNotification,
                      animationStyle : int = CWNotificationAnimationStyleTop,
                      animationType : int = CWNotificationAnimationTypeReplace,
                      onTapCallback : callable = None, # the function to call if user taps notification -- should return None and take no args
                      multiline : bool = False) -> None:
    global cw_notif_blocks
    cw_notif = MyNotif.new().autorelease()
    
    def onTap() -> None:
        #print("onTap")
        if onTapCallback is not None: onTapCallback()
        if not cw_notif.notificationIsDismissing:
            cw_notif.dismissNotification()
        
    if color is None or len(color) != 4 or [c for c in color if type(c) is not float]:
        color = (0.0, 122.0/255.0, 1.0, 1.0)
      
    # set default blue color (since iOS 7.1, default window tintColor is black)
    cw_notif.notificationLabelBackgroundColor = UIColor.colorWithRed_green_blue_alpha_(*color)
    cw_notif.notificationStyle = style
    cw_notif.notificationAnimationInStyle = animationStyle
    cw_notif.notificationAnimationOutStyle = animationStyle
    cw_notif.notificationAnimationType = animationType
    cw_notif.multiline = multiline
    message = str(message)
    duration = float(duration)
    blk = Block(onTap)
    cw_notif_blocks[cw_notif.ptr.value] = blk
    cw_notif.notificationTappedBlock = blk
    cw_notif.displayNotificationWithMessage_forDuration_(message, duration)
    