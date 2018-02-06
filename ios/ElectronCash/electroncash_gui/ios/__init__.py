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

import signal
import sys
import traceback


try:
    import toga
except Exception:
    sys.exit("Error: Could not import toga")


from electroncash.i18n import _, set_language
#from electroncash.plugins import run_hook
from electroncash import WalletStorage
# from electroncash.synchronizer import Synchronizer
# from electroncash.verifier import SPV
# from electroncash.util import DebugMem
from electroncash.util import UserCancelled, print_error
# from electroncash.wallet import Abstract_Wallet

#from .installwizard import InstallWizard, GoBack

def check_imports():
    # pure-python dependencies need to be imported here for pyinstaller
    try:
        import dns
        import pyaes
        import ecdsa
        import requests
        import qrcode
        import pbkdf2
        import google.protobuf
        import jsonrpclib
        # the following imports are for pyinstaller
        from google.protobuf import descriptor
        from google.protobuf import message
        from google.protobuf import reflection
        from google.protobuf import descriptor_pb2
        from jsonrpclib import SimpleJSONRPCServer
        import electroncash
        import electroncash.bitcoin
    # make sure that certificates are here
    except ImportError as e:
        return "Error: %s"%str(e)

    try:
        thekey = "5Hwpw2vSB66RMzf74b8isUYZFfQ23yrrmotVrxmJVcnjBDwWZ76"
        return thekey + " decodes to: " + electroncash.bitcoin.address_from_private_key(str.encode(thekey,'utf8'))
    except Exception as e:
        print("Error: %s"%str(e))
        return str(e)
    #NOT REACHED..
    #return "ALL OK!"


class ElectrumGui(toga.App):

    def __init__(self, config, daemon, plugins):
        super().__init__('Electron-Cash', 'com.c3-soft.ElectronCash')
        set_language(config.get('language'))
        # Uncomment this call to verify objects are being properly
        # GC-ed when windows are closed
        #network.add_jobs([DebugMem([Abstract_Wallet, SPV, Synchronizer,
        #                            ElectrumWindow], interval=5)])
        self.config = config
        self.daemon = daemon
        self.plugins = plugins
        #run_hook('init_qt', self)

    def init_network(self):
        # Show network dialog if config does not exist
        if self.daemon.network:
            if self.config.get('auto_connect') is None:
                #wizard = InstallWizard(self.config, self.app, self.plugins, None)
                #wizard.init_network(self.daemon.network)
                #wizard.terminate()
                print("NEED TO SHOW WIZARD HERE")
                pass

    def calculate(self, widget):
        try:
            self.c_input.value = (float(self.f_input.value) - 32.0) * 5.0 / 9.0
        except Exception:
            self.c_input.value = '???'

    def startup(self):
        self.main_window = toga.MainWindow(self.name)
        self.main_window.app = self

        # Tutorial 1
        c_box = toga.Box()
        f_box = toga.Box()
        box = toga.Box()

        self.c_input = toga.TextInput(readonly=True)
        self.f_input = toga.TextInput()

        c_label = toga.Label('Celsius', alignment=toga.LEFT_ALIGNED)
        f_label = toga.Label('Fahrenheit', alignment=toga.LEFT_ALIGNED)
        join_label = toga.Label('is equivalent to', alignment=toga.RIGHT_ALIGNED)

        button = toga.Button('Calculate', on_press=self.calculate)

        f_box.add(self.f_input)
        f_box.add(f_label)

        c_box.add(join_label)
        c_box.add(self.c_input)
        c_box.add(c_label)

        box.add(f_box)
        box.add(c_box)
        box.add(button)

        slbl = toga.Label(check_imports(), alignment=toga.LEFT_ALIGNED)
        slbl.set_font(toga.Font(family="Helvetica",size=10.0))

        box.add(slbl)

        box.style.set(flex_direction='column', padding_top=10)
        f_box.style.set(flex_direction='row', margin=5)
        c_box.style.set(flex_direction='row', margin=5)

        self.c_input.style.set(flex=1)
        self.f_input.style.set(flex=1, margin_left=160)
        c_label.style.set(width=100, margin_left=10)
        f_label.style.set(width=100, margin_left=10)
        join_label.style.set(width=150, margin_right=10)
        button.style.set(margin=15)
        
        self.main_window.content = box
        self.main_window.show()


    def main(self):
        try:
            self.init_network()
        except:
            traceback.print_exc(file=sys.stdout)
            return
        self.config.open_last_wallet()
        path = self.config.get_wallet_path()
        print("WALLET PATH: %s"%path)
        #if not self.start_new_window(path, self.config.get('url')):
        #    return
        signal.signal(signal.SIGINT, lambda *args: self.exit())
        # main loop
        # note that on iOS this is a no-op and returns right away
        self.main_loop()
        
        
