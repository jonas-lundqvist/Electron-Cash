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

def show_alert(vc : ObjCInstance, # the viewcontroller to present the alert view in
               title : str, # the alert title
               message : str, # the alert message
               # actions is a list of lists: each element has:  Button names, plus optional callback spec
               # each element of list is [ 'ActionTitle', callable, arg1, arg2... ] for optional callbacks
               actions: list = [ ['Ok'] ],  # default has no callbacks and shows Ok button
               cancel: str = None, # name of the button you want to designate as 'Cancel' (ends up being first)
               destructive: str = None, # name of the button you want to designate as destructive (ends up being red)
               alertStyle: int = UIAlertControllerStyleAlert,
               completion: callable = None # optional completion function that gets called when alert is presented
               ) -> None:
    global callables_tmp
    global completion_tmp
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
    for i,arr in enumerate(actions):
        if type(arr) is list or type(arr) is tuple:
            actTit = arr[0]
            fun_args = arr[1:]
            callables_tmp[actTit] = fun_args
        else:
            actTit = arr
        style = UIAlertActionStyleCancel if actTit == cancel else UIAlertActionStyleDefault
        style = UIAlertActionStyleDestructive if actTit == destructive else style
        act = HelpfulGlue.actionWithTitle_style_python_(actTit,style,'''
import electroncash_gui.ios_native.utils as u

if u.callables_tmp.get(action_title):
    arr = u.callables_tmp[action_title]
    fun = arr[0]
    fun(*arr[1:])
''')
        alert.addAction_(act)
    if completion is not None:
        completion_tmp = completion
        HelpfulGlue.viewController_presentModalViewController_animated_python_(vc,alert,True,'''
import electroncash_gui.ios_native.utils as u
if u.completion_tmp is not None:
    u.completion_tmp()
    u.completion_tmp = None
''')
    else:
        HelpfulGlue.viewController_presentModalViewController_animated_python_(vc,alert,True,None)




