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

# Useful for having python call anything (including obj-c-backed python classes) off of the mainLoop/timer
# sometime in the future.
# Note: unlike the other functions above -- this *can* be used from any thread and the callback will always
#       run in the Main Thead!  This is useful for calling into the GUI from a separate thread, for example.
calllater_table = {}
def call_later(timeout : float, func : callable, *args) -> None:
    python = '''
import electroncash_gui.ios_native.utils as u

if u.calllater_table.get(timer_ptr):
    f = u.calllater_table[timer_ptr][0]
    if f is not None:
        argz = u.calllater_table[timer_ptr][1:]
        f(*argz)
    del u.calllater_table[timer_ptr]
'''
    global calllater_table
    ptr =  HelpfulGlue.evalPython_afterDelay_(python,timeout,True)
    calllater_table[ptr] = [func,*args]

