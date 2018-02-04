import toga

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

def get_user_dir():
    import rubicon.objc
    NSFileManager = rubicon.objc.ObjCClass('NSFileManager')
    dfm = NSFileManager.defaultManager
    # documents dir
    dir = dfm.URLsForDirectory_inDomains_(9, 1).objectAtIndex_(0)
    return str(dir.path)

class Converter(toga.App):

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


def main():
    print("HomeDir from ObjC --> '%s'"%get_user_dir())

    from electroncash.simple_config import SimpleConfig
    from electroncash import daemon
    sc = SimpleConfig(read_user_dir_function=get_user_dir)
    fd, server = daemon.get_fd_or_server(sc)
    print (" server=%s"%str(server))


    return Converter('Electron-Cash', 'com.c3-soft.ElectronCash')
