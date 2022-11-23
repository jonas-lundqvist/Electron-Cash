#!/usr/bin/env python3

import subprocess
import shutil
import tempfile
import time
import os
import platform
from typing import Any, Generator
import pytest
import requests

from bitcoinrpc.authproxy import AuthServiceProxy
from jsonrpcclient import parse as rpc_parse, request
from jsonpath_ng import parse as path_parse

datadir = ""
bitcoind = None

SUPPORTED_PLATFORM = platform.machine() in ("AMD64", "x86_64") and platform.system() in "Linux"

EC_DAEMON_RPC_URL = "http://user:pass@localhost:12342"
FULCRUM_STATS_URL = "http://localhost:8081/stats"
BITCOIND_RPC_URL = "http://user:pass@0.0.0.0:18333"

def poll_for_answer(url: Any, json_req: Any = None, expected_answer: Any = None, poll_interval: int = 1, poll_timeout: int = 10) -> Any:
    """ Poll an RPC method until timeout or an expected answer has been received """
    start = current = time.time()

    while current < start + poll_timeout:
        retry = False
        try:
            if json_req is None:
                resp = requests.get(url)
                json_result = resp.json()
            else:
                resp = requests.post(url, json=json_req)
                if resp.status_code == 500:
                    retry = True
                else:
                    json_result = rpc_parse(resp.json()).result

            if expected_answer is not None and not retry:
                path, answer = expected_answer
                jsonpath_expr = path_parse(path)
                expect_element = jsonpath_expr.find(json_result)
                if len(expect_element) > 0 and expect_element[0].value == answer:
                    return json_result
            elif retry:
                pass
            else:
                return json_result
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(poll_interval)
        current = time.time()

def bitcoind_rpc_connection() -> AuthServiceProxy:
    """ Connects to bitcoind, generates 100 blocks and returns the connection """
    bitcoind = AuthServiceProxy(BITCOIND_RPC_URL)

    poll_for_answer(BITCOIND_RPC_URL, request('uptime'))
    block_count = bitcoind.getblockcount()
    if block_count < 101:
        bitcoind.generate(101)

    return bitcoind

# Creates a temp directory on disk for wallet storage
# Starts a deamon, creates and loads a wallet
def start_ec_daemon() -> None:
    """
    Creates a temp directory on disk for wallet storage
    Starts a deamon, creates and loads a wallet
    """
    if datadir is None:
        assert False
    os.mkdir(datadir + "/regtest")
    shutil.copyfile("electroncash/tests/regtest/configs/electron-cash-config", datadir + "/regtest/config")
    environ = os.environ.copy()
    environ["COVERAGE_FILE"] = ".coverage-regtest"
    subprocess.run(["python3", "-m", "coverage", "run", "electron-cash", "--regtest", "-D", datadir, "-w", datadir+"/default_wallet", "daemon", "start"], check=True, env=environ)
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('version'))

    from ...version import PACKAGE_VERSION
    assert result == PACKAGE_VERSION

    r = request('create', params={"wallet_path": datadir+"/default_wallet"})
    result = poll_for_answer(EC_DAEMON_RPC_URL, r)
    assert "seed" in result
    assert len(result["seed"].split(" ")) == 12

    result = poll_for_answer(EC_DAEMON_RPC_URL, request('load_wallet'))
    assert result

    # Wait until the wallet is up to date
    poll_for_answer(EC_DAEMON_RPC_URL, request('getinfo'), expected_answer=("wallets[\""+datadir+"/default_wallet\"]", True))

def stop_ec_daemon() -> None:
    """ Stops the daemon and removes the wallet storage from disk """
    subprocess.run(["./electron-cash", "--regtest", "-D", datadir, "daemon", "stop"], check=True)
    if datadir is None or datadir.startswith("/tmp") is False:  # Paranoia
        assert False
    shutil.rmtree(datadir)

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig) -> str:
    """ Needed since the docker-compose.yml is not in the root directory """
    return os.path.join(str(pytestconfig.rootdir), "electroncash/tests/regtest/docker-compose.yml")

@pytest.fixture(scope="session")
def fulcrum_service(docker_services: Any) -> Generator[None, None, None]:
    """ Makes sure all services (bitcoind, fulcrum and the EC daemon) are up and running """
    global datadir
    global bitcoind
    datadir = tempfile.mkdtemp()
    bitcoind = bitcoind_rpc_connection()
    poll_for_answer(FULCRUM_STATS_URL, expected_answer=('Controller.TxNum', 102))

    start_ec_daemon()
    yield
    stop_ec_daemon()

@pytest.mark.skipif(not SUPPORTED_PLATFORM,
                    reason="Unsupported platform")
def test_getunusedaddress(fulcrum_service: Any) -> None:
    """ Verify the `getunusedaddress` RPC """
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('getunusedaddress'))

    # The daemon does not return a prefix.
    # Check that the length is 42 and starts with 'q'
    assert len(result) == 42
    assert result[0] == 'q'

@pytest.mark.skipif(not SUPPORTED_PLATFORM,
                    reason="Unsupported platform")
def test_getservers(fulcrum_service: Any) -> None:
    """ Verify the `getservers` RPC """
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('getservers'))

    # Only one server in this setup
    assert len(result) == 1

@pytest.mark.skipif(not SUPPORTED_PLATFORM,
                    reason="Unsupported platform")
def test_balance(fulcrum_service: Any) -> None:
    """ Verify the `getbalance` RPC """
    addr = poll_for_answer(EC_DAEMON_RPC_URL, request('getunusedaddress'))

    bitcoind.generatetoaddress(1, addr)
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('getbalance'), expected_answer=('unmatured', '50'))
    assert result['unmatured'] == '50'

    bitcoind.sendtoaddress(addr, 10)
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('getbalance'), expected_answer=('unconfirmed', '10'))
    assert result['unmatured'] == '50' and result['unconfirmed'] == '10'

    bitcoind.generate(1)
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('getbalance'), expected_answer=('confirmed', '10'))
    assert result['unmatured'] == '50' and result['confirmed'] == '10'

    bitcoind.generate(97)
    bitcoind.sendtoaddress(addr, 10)
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('getbalance'), expected_answer=('unconfirmed', '10'))
    assert result['unmatured'] == '50' and result['confirmed'] == '10' and result['unconfirmed'] == '10'

    bitcoind.generate(1)
    result = poll_for_answer(EC_DAEMON_RPC_URL, request('getbalance'), expected_answer=('confirmed', '70'))
    assert result['confirmed'] == '70'
