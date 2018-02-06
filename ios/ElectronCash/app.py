#!/usr/bin/env python3

def get_user_dir():
    import rubicon.objc
    NSFileManager = rubicon.objc.ObjCClass('NSFileManager')
    dfm = NSFileManager.defaultManager
    # documents dir
    dir = dfm.URLsForDirectory_inDomains_(9, 1).objectAtIndex_(0)
    return str(dir.path)

def prompt_password(prmpt, dummy):
    from electroncash_gui.ios_native import ElectrumGui
    return ElectrumGui.prompt_password(prmpt, dummy)


def main():
    print("HomeDir from ObjC --> '%s'"%get_user_dir())

    try:
        import sys, os
        from electroncash.commands import get_parser, known_commands, Commands, config_variables
        from electroncash.simple_config import SimpleConfig
        from electroncash import daemon
        from electroncash import bitcoin
        from electroncash import SimpleConfig, Network
        from electroncash.networks import NetworkConstants
        from electroncash.wallet import Wallet, ImportedPrivkeyWallet, ImportedAddressWallet
        from electroncash.storage import WalletStorage
        from electroncash.util import print_msg, print_stderr, json_encode, json_decode
        from electroncash.util import set_verbosity, InvalidPassword
        from electroncash.commands import get_parser, known_commands, Commands, config_variables
        from electroncash import daemon
        from electroncash import keystore
        from electroncash.mnemonic import Mnemonic
        #import electroncash_plugins
        import electroncash.web as web
    except Exception as e:
        print("ec_main exception: %s"%str(e))
        return None

    def run_non_RPC(config):
        cmdname = config.get('cmd')

        storage = WalletStorage(config.get_wallet_path())
        if storage.file_exists():
            sys.exit("Error: Remove the existing wallet first!")

        def password_dialog():
            return prompt_password("Password (hit return if you do not wish to encrypt your wallet):")

        if cmdname == 'restore':
            text = config.get('text').strip()
            passphrase = config.get('passphrase', '')
            password = password_dialog() if keystore.is_private(text) else None
            if keystore.is_address_list(text):
                wallet = ImportedAddressWallet.from_text(storage, text)
            elif keystore.is_private_key_list(text):
                wallet = ImportedPrivkeyWallet.from_text(storage, text, password)
            else:
                if keystore.is_seed(text):
                    k = keystore.from_seed(text, passphrase, False)
                elif keystore.is_master_key(text):
                    k = keystore.from_master_key(text)
                else:
                    sys.exit("Error: Seed or key not recognized")
                if password:
                    k.update_password(None, password)
                storage.put('keystore', k.dump())
                storage.put('wallet_type', 'standard')
                storage.put('use_encryption', bool(password))
                storage.write()
                wallet = Wallet(storage)
            if not config.get('offline'):
                network = Network(config)
                network.start()
                wallet.start_threads(network)
                print_msg("Recovering wallet...")
                wallet.synchronize()
                wallet.wait_until_synchronized()
                msg = "Recovery successful" if wallet.is_found() else "Found no history for this wallet"
            else:
                msg = "This wallet was restored offline. It may contain more addresses than displayed."
            print_msg(msg)

        elif cmdname == 'create':
            password = password_dialog()
            passphrase = config.get('passphrase', '')
            seed_type = 'standard'
            seed = Mnemonic('en').make_seed(seed_type)
            k = keystore.from_seed(seed, passphrase, False)
            storage.put('keystore', k.dump())
            storage.put('wallet_type', 'standard')
            wallet = Wallet(storage)
            wallet.update_password(None, password, True)
            wallet.synchronize()
            print_msg("Your wallet generation seed is:\n\"%s\"" % seed)
            print_msg("Please keep it in a safe place; if you lose it, you will not be able to restore your wallet.")

        wallet.storage.write()
        print_msg("Wallet saved in '%s'" % wallet.storage.path)
        sys.exit(0)


    #sc = SimpleConfig(read_user_dir_function=get_user_dir)
    #fd, server = daemon.get_fd_or_server(sc)
    #print (" server=%s"%str(server))
    script_dir = os.path.dirname(os.path.realpath(__file__))
    is_bundle = getattr(sys, 'frozen', False)
    print("script_dir = '%s'\nis_bunde = %s"%(script_dir, str(is_bundle)))
    #for k,v in os.environ.items():
    #print("Env '%s' = '%s'" % (k, v))

    # on osx, delete Process Serial Number arg generated for apps launched in Finder
    sys.argv = list(filter(lambda x: not x.startswith('-psn'), sys.argv))

    # old 'help' syntax
    if len(sys.argv) > 1 and sys.argv[1] == 'help':
        sys.argv.remove('help')
        sys.argv.append('-h')

    # read arguments from stdin pipe and prompt
    for i, arg in enumerate(sys.argv):
        if arg == '-':
            if not sys.stdin.isatty():
                sys.argv[i] = sys.stdin.read()
                break
            else:
                raise BaseException('Cannot get argument from stdin')
        elif arg == '?':
            sys.argv[i] = input("Enter argument:")
        elif arg == ':':
            sys.argv[i] = prompt_password('Enter argument (will not echo):', False)

    # parse command line
    parser = get_parser()
    args = parser.parse_args()

    # config is an object passed to the various constructors (wallet, interface, gui)
    config_options = {
            'verbose': True,
            'cmd': 'gui',
            'gui': 'ios_native',
    }

    config_options['cwd'] = os.getcwd()

    # fixme: this can probably be achieved with a runtime hook (pyinstaller)
    try:
        if is_bundle and os.path.exists(os.path.join(sys._MEIPASS, 'is_portable')):
            config_options['portable'] = True
    except AttributeError:
        config_options['portable'] = False

    if config_options.get('portable'):
        config_options['electron_cash_path'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'electron_cash_data')

    # kivy sometimes freezes when we write to sys.stderr
    set_verbosity(config_options.get('verbose') and config_options.get('gui')!='kivy')

    if config_options.get('testnet'):
        NetworkConstants.set_testnet()

    # check uri
    uri = config_options.get('url')
    if uri:
        if not uri.startswith(NetworkConstants.CASHADDR_PREFIX + ':'):
            print_stderr('unknown command:', uri)
            sys.exit(1)
        config_options['url'] = uri

    for k,v in config_options.items():
        print("config[%s] = %s"%(str(k),str(v)))

    # todo: defer this to gui
    config = SimpleConfig(config_options,read_user_dir_function=get_user_dir)
    cmdname = config.get('cmd')

    # run non-RPC commands separately
    if cmdname in ['create', 'restore']:
        run_non_RPC(config)
        sys.exit(0)

    if cmdname == 'gui':
        fd, server = daemon.get_fd_or_server(config)
        print("fd=%s server=%s"%(str(fd),str(server)))
        if fd is not None:
            plugins = None
            #plugins = init_plugins(config, config.get('gui', 'qt'))
            d = daemon.Daemon(config, fd, True)
            d.start()
            d.init_gui(config, plugins)
            #sys.exit(0)
        else:
            result = server.gui(config_options)

    return "Bitcoin Cash FTW!"
