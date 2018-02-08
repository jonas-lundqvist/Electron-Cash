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
import bz2
import base64


try:
    from .uikit_bindings import *
except Exception as e:
    sys.exit("Error: Could not import iOS libs: %s"%str(e))


from electroncash.i18n import _, set_language
#from electroncash.plugins import run_hook
from electroncash import WalletStorage, Wallet
# from electroncash.synchronizer import Synchronizer
# from electroncash.verifier import SPV
# from electroncash.util import DebugMem
from electroncash.util import UserCancelled, print_error

# from electroncash.wallet import Abstract_Wallet

# a dummy hard coded wallet with a few tx's in its history for testing
# encrypted with password 'bchbch'
hardcoded_testing_wallet = bz2.decompress(base64.b64decode(b'QlpoOTFBWSZTWa8y9/wAA4EfgAAI/+A////wP///8GAKW2Sdfbe9933c77fL73t9977vvnd9d3e+n0+vT77tuu99vXZ9997314yp+jGoyaYEMmJ6p4aaNEYJtATyqGVPyp+aTEYIzSn6Jmiaangyam0AJT9UOp+jDSaZNoTRgm0xGmiYT1MBBIZU9gTGgKexANTRiaYR6ATJhUOp71MVP9Gk9DJNU/EwFNtACNkqewj1UFVT/QGSMTJtBNqMmJiZMFPAI9FSCwm5SflhzKS6OfFvvvt8TLCfX6R9FTi9sNGVM25kmyEUoI+9LoFmfxNo4bEKdBefXQWOe20Pp7LCTguKtunJljE1MMMt1RkDDSqZ5LBiO1aDTgR/Z8WDK6cSUE84T9XIIxCVnLSgDBl31enW93/UPAAl1rMaL2mkp+6cB7cICrW43jgL/Xol364qQKtyFAK+cdB5+nuXP7q0IYY6L9iucOA73FScfydvt/AGI9xCqctOwOjJHFN1pr4JO6iMIuyfNsNwLyVbPeyr7kO5kqMAeWskf3SDF9kcw150pjiXDv4RLHG5kc6+cRBlbB5jxZ5tWJmmd5W6ekMMCu6cYoIasPPPVfowLzSwop3UdMAC10BniCeY2HkmrNWGPXujmPpkTW/brd6ubgHqTYs5zrzRlh8mFQzQzqw5Rval0LynLFfFviPvQlzA7NHv1jDwaTfmFDZfQO3C/w3hd5LHk09+0lg1pMwgdI2nb981ONZsqCSoObGc32NcFH96ElgORPBJCVOIzXu2R2u/fyfJtpVT+K6OEDBb/3S7ms1vUcXt+7t9P9d95P4Fo/xCYv0L+akzsB2V4mxPgGHnZue196THc4st2Bn+MEJjT68j2r56XC4ss3J4QwA9YZeuVj/COxiRyFazs7+wdD2E3TWnPsvKWuGT2B6F+E0XKTmiZwQUiD+LsIVVDDmXXs3llLDF/iaRS3+A4tIPbMwWsFOqUkvmjyCZhsIqPhqlv602Zg9+5sfXK7ecNX82dAr/SevFCBSdnyt0p7iwsKp3W0FX2G9UEul5s/7VlLjxWQ6cw6Ep31TfB4pDTvBZ6EWoBKtjFN23rb+WMohz0uuO2rgamzmSnQGBw1oynLRbvnYihz4+UJxSQNM9gsE8hruiRiqmMzbYpOswwn6hk35P7VZrhYDPTbEJlb7B03TJRdwNzrjfOmSRdeL4IgVufvP4GcAoMKh4s4+x26nrehZZaygugg3bQ/W0C7N3e+0zo9Z6jSxaClu+CMX28U/xuiNIJp2exHfrlNdsG0UmT77XT1lPyFvB2Pk8giaIYykQyZwYAZBxj3kH42uOuWSKpdyW5I9Pw3sYriYt9jIUxNanEW63vs82O/FQL2ffIrFZTxDRtCB0N1If5mPWjYF6zTrqHAwj8RWpTL56vMWJ6ud/ziHi1Rhen79M1geisLalrhB3QbxZqsb7mKReHdLfbEeafUIagf0qV7UWg19MB0c4B2FUbB+3UjA6IdhOehYZKYcwDzWsXsnEJ9r067lfV3yq3M44IJJecpOkg5jZPh8Z63XsQBcoWxTxDUQOcpN8SFJn0xtBc6+ra8tp83L/XXSsWo0KYhPIg8DIPHLpC2aydrW05cvvb0N347KOYfCefqPzNLUHaHlKYJF+vihGrQLFjZRAx9q/T7qnuvdTX/kAwtmwIVr9qOAxAYEf6SDf8RaWl4u28oW2fK1Hwx1A1crYpH1F43qLphtON095AWNvByNo60l7d0qGBlwdyAJCmg0JSu8tSQ98TOWBW6eGr0K1MYP62ydUnv41ZDzfqsUdr3AOAfqGF4TKo667DM7YhPlbRo+LdsjkvqC56A8J9HpuKpVg7eV5vml7v3uLMnmzhwVNFDx1HDgBohvGLiOmWcOM10gn10rrwTYU9/CRE9g0h8O0H/Qb76cpmqZVEk8eG9desyXJfEg+JOVkpedyoCqqfCESf7m7odUAyKGftnHIcUzkwVLsnVjR1nuw36n+ngwwgIF6OmXU9PL44+BZCkJa1b2Qx56ldCdfo7Xv51AvrChntbBenYIYbJl4WZkwUDQ6e/vzSHGAsiHi7WQZ7fR+fTiz123SWCXRRwRdqAT4PfVZyBrMiryMHZlk/sRLn5Z+2y9yQY/Ytg2pQpJDoqs33IsGOi/denfYAhS9fS43Gtp0oD7lTJnXyzf2h4jsjRAR08xdc0GKaIAbwsceo++/KKUyAjVAt65LRUqveCOfs1Djzk2My9dY5W1y6w8XHMvm+sPzQiiAjd8tojvHvIKP3Q0od4I25yek7QgMYzkf49GkfPhU2JnTeTJDP2zF8CjZuXu8ki02aq+ryUE4avEBk1Yu9ngXy4AU5LU09qmt/kVUE0hck9c8eXBFPh6vvcKfjOVv21xJVvmOt8MF0NIxyP47h6TWdUz+rHd7nNH7Co1y4flvRAnyd7jKj8yjqPcvPtLxDDw2vqd5EQ0+7QuIVeuApCrt4lfV3BRTApMEfQ3kSP0G4pS1o4zy5M1S6hau6ngmtvexmOw+5XkHXh+BCtvKh1tg5ghzAH016zZRBgT3wU5w3qA81vvdzfUByZXbxMsxkGPbKWTfZFH71ktm9nnWlrcY70fs8tPsM6DUm3wi0LkzeO7uWmeTDDUry9MCs+0ya1+xRygm6Hij5V8w6tWNUFwP99rWEdNucfVR7IbvzEkmMYE5v29mP1OJ9TbCAFHSVCTCkm8mIrKesUbZEMZBzrD8jd7Fs3rw7Ig84ePkcVFyT/ULteiisnxDiOIoMimgxHfO6RYyOqVvjJTN8r6m8k0aykv5xsfakxPNFArQfZ27+DdWcbRwPqj5OazRuDw+MwzSmGixWhVAGtCjVi67mQWf8xz7C7fnE46OkC3MOFBsQWQnMzZX/oeO4V3IlexdmuB9b6z1Z03z8dVwa+JzbSjLZH4hvs41mq8hvOXPI/1r8tAhS9EM54UckOnnNjFoF3PpTUgul54WD2GpGa/2AdNIMUXypf0dCyX3AMS5MfMZR65xo+Du4oyH3zRMwz9FYcPUSqzaVCQ7aLr8k8icJcOHRm5SOPB7GwOCR0Po3PJOqxchRIeo4KzfaBd/yUBLBjU+Z81ZJVLGWzNPo+HFIEbYMiZMH1uRQkBYdPWU+EWo7MIO/VamuwQl/84SpNrg1JsBCB11nq0EGi3SWIbRWBBHVZfCaC/HuZgRT8rrbaqJawNoC49PrfPHnZdxfJiTZV54Fz7PwzGG1A+VDgay2RyNpKz/XKIT/ostOC26JFvbZuGEgEZJul8uKmf50kfoNxkO97SGejwPy3rrz/cHDm8rbd+UzNBtgE7/IOLcSLkdbvvPcuJCZpplkp7bK7PakWOrOXrbNOCGZS6ggC10PLZ1lQhXHmhwFrIcbwm3aiyB2iWqbza/Z+LIBPQUmyJQ1qD/cyWwCrfZe67fxdK0zow8I6N43ZYynbfr7TcEHMy+n4ZJtcmHO3jwQcAbwUutyUcQTNl2BBJ/ATZnTanbqB47z/uoXzLWW27chKpSpKU9+gm4/iHjwRRd9Vc7KMmOdqZaifpRWqI5sGefGA6mFg9EEPe71GcjGVIMBLNdae9bJqGgLaRV53ZhU4zravpEXdvJVWL7lBRshjE/yQF6AyTD5PQyat6z+iJZsIUT9C3iZKsPpW9Sc44WGbdlNZXYtpPvSvo0AUr+lLBEOnF4zBVq2OpAxo0KoYcy81KsqvNwY7sq7wLjkup6QWDtJs9rI9gRLnd/fKbm6yMT8pt8GzebEiH8SaUD0sM5K5XmiEkxE8kQaUsFy8RoQKA/rJ4+slYePmYpKrJxsd7d3yGqz4+1u8/o7jcG4RTRhXJaw2zTZFNugvCTJ+XsNJG4Dc9g/WxLQsEsl8g+bo0DNP9ZGNPS0gv/j653sIbUjcR3Da8b8KIci5n25CS7YzT0KL8BAAyP4GNRmrFn2yKntQxh1osnbra85R04TV1L0BQsa96QI3VPqPktojrlPii2DQ/eNObMQFOWXkea3MLrNR2HYT8rq35kyw4SazzN1rbd8TPej/bJcWkQNJ0h4MFJ+comMLThNTK9MRHwKYKOa5g7RyynYv6mWuHz5bQ71Tl/ScJoqdLI9aVYkoJb3ckb/nAbZZVAVYTPaBKxquJ1UAX3mErkygYj9dbjp+PzTeMv5St2wq0MTDS4yPkOe2h3qlsZPrp6mW3Y3a/YBM1g+rZ9KpglD1qGoT7LoXqKnaxzl9WETc/3EevtKuBc5D6ie8dg81yarFY8LY4MzBBPUp/xdyRThQkK8y9/wA=='))

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


class ElectrumGui:

    gui = None

    def __init__(self, config, daemon, plugins):
        ElectrumGui.gui = self
        self.appName = 'Electron-Cash'
        self.appDomain = 'com.c3-soft.ElectronCash'
        set_language(config.get('language'))
        # Uncomment this call to verify objects are being properly
        # GC-ed when windows are closed
        #network.add_jobs([DebugMem([Abstract_Wallet, SPV, Synchronizer,
        #                            ElectrumWindow], interval=5)])
        self.config = config
        self.daemon = daemon
        self.plugins = plugins
        self.wallet = None
        self.mleText = ''
        self.headings = ()
        self.history = ()
        self.screen = None
        self.window = None
        self.controller = None

    def createUIAndShow(self):
        if not self.screen:
            self.screen = UIScreen.mainScreen
        if not self.window:
            self.window = UIWindow.alloc().initWithFrame_(self.screen.bounds)
        if not self.controller:
            self.controller = UIViewController.alloc().init()

        self.window.backgroundColor = UIColor.whiteColor
        self.window.rootViewController = self.controller

        lbl = UILabel.alloc().initWithFrame_(self.screen.bounds)
        lbl.text = str(check_imports())
        self.controller.view = lbl
        self.window.makeKeyAndVisible()
        return True

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

    @staticmethod
    def prompt_password(prmpt, dummy=0):
        print("prompt_password(%s,%s)"%(prmpt,str(dummy)))
        return "bchbch"


    def generate_wallet(self, path):
        with open(path, "wb") as fdesc:
            fdesc.write(hardcoded_testing_wallet)
            fdesc.close()
            print("Generated hard-coded wallet -- wrote %d bytes"%len(hardcoded_testing_wallet))
        storage = WalletStorage(path, manual_upgrades=True)
        if not storage.file_exists():
            return
        if storage.is_encrypted():
            password = ElectrumGui.prompt_password("EnterPasswd",0)
            if not password:
                return
            storage.decrypt(password)
        if storage.requires_split():
            return
        if storage.requires_upgrade():
            return
        if storage.get_action():
            return
        wallet = Wallet(storage)
        return wallet

    def do_wallet_stuff(self, path, uri):
        try:
            wallet = self.daemon.load_wallet(path, ElectrumGui.prompt_password("PassPrompt1"))
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            return
        if not wallet:
            storage = WalletStorage(path, manual_upgrades=True)
            try:
                wallet = self.generate_wallet(path)
            except Exception as e:
                print_error('[do_wallet_stuff] Exception caught', e)
            if not wallet:
                return
            wallet.start_threads(self.daemon.network)
            self.daemon.add_wallet(wallet)
        print("WALLET=%s"%str(wallet))
        return wallet

    # this method is called by Electron Cash libs to start the GUI, but we defer actual GUI
    # creation until applicationDidFinishLaunching, as that's when we are guaranteed to have all
    # objc classes...
    def main(self):
        try:
            self.init_network()
        except:
            traceback.print_exc(file=sys.stdout)
            return
        self.config.open_last_wallet()
        path = self.config.get_wallet_path()


        # hard code some stuff for testing
        self.daemon.network.auto_connect = True
        self.config.set_key('auto_connect', self.daemon.network.auto_connect, True)
        print("WALLET PATH: %s"%path)
        print ("NETWORK: %s"%str(self.daemon.network))
        w = self.do_wallet_stuff(path, self.config.get('url'))

        # TODO: put this stuff in the UI
        if not w:
            sys.exit(1)
            return
        self.wallet = w
        hist = w.get_history()
        i=0
        self.mleText = check_imports()
        self.headings = ("TxHash","Height","Conf","TimeStamp","Delta","Balance");
        self.history = hist
        for a in hist:
            ss = "history[%d] tx_hash=%s height=%d, conf=%d, timestamp=%s, delta=%s, balance=%s"%(i,*a)
            print(ss)
            i=i+1
        signal.signal(signal.SIGINT, lambda *args: self.exit())

class PythonAppDelegate(UIResponder):
    @objc_method
    def applicationDidBecomeActive(self) -> None:
        print("App became active.")

    @objc_method
    def application_didFinishLaunchingWithOptions_(self, application, launchOptions) -> bool:
        print("App finished launching.")
        if ElectrumGui.gui:
            return ElectrumGui.gui.createUIAndShow()
        return False

    @objc_method
    def application_didChangeStatusBarOrientation_(self, application, oldStatusBarOrientation: int) -> None:
        print("ROTATED", oldStatusBarOrientation)
            #App.app.main_window.content._update_layout(
            #                                       width=App.app.main_window._screen.bounds.size.width,
            #                                       height=App.app.main_window._screen.bounds.size.height,
            #                                       )

