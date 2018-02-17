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
try:
    from .uikit_bindings import *
except Exception as e:
    sys.exit("Error: Could not import iOS libs: %s"%str(e))

bundle_identifier = NSBundle.mainBundle.bundleIdentifier
bundle_domain = '.'.join(bundle_identifier.split('.')[0:-1])
bundle_short_name = bundle_domain + ".ElectronCash"
imgs_subdir = "Library/Application Support/" + bundle_short_name + "/app/ElectronCash/electroncash_gui/ios_native/imgs"

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

def get_bundle_image_path(fileName: str) -> str:
    return get_bundle_resource_path(fileName, imgs_subdir)

def uiimage_get(fileName: str) -> ObjCInstance:
    fn, ext = get_fn_and_ext(fileName)
    img = UIImage.imageNamed_(fn) # try and get the 'cached' image from resources folder -- faster
    if img is not None:
        return img
    if is_2x_screen() and not fn.endswith('@2x'):
        fileName2x = fn + '@2x' + '.' + ext
        f=get_bundle_image_path(fileName2x)
        if f is not None:
            return UIImage.alloc().initWithContentsOfFile_(f).autorelease()
    f=get_bundle_image_path(fileName)
    return UIImage.alloc().initWithContentsOfFile_(f).autorelease()
