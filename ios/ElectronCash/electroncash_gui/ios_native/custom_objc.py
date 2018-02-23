import sys

try:
    from .uikit_bindings import *
except Exception as e:
    sys.exit("Error: Could not import iOS libs: %s"%str(e))


QRCodeReader = ObjCClass('QRCodeReader')
QRCodeReaderViewController = ObjCClass('QRCodeReaderViewController')
HelpfulGlue = ObjCClass('HelpfulGlue')