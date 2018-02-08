# This line needs to be here becasue the iOS main.m evaluates this script and looks for a
# Python class (that is bridged to ObjC) named "PythonAppDelegate", which gets the
# 'applicationDidFinishLaunchingWithOptions' call, which is really where we start the app.
import electroncash_gui.ios_native.appdelegate

if __name__ == '__main__':
    # This is a noop.. for app entry point see electroncash_gui/ios_native/appdelegate.py, which ends up calling
    # ElectronCash/app.py main()
    pass
