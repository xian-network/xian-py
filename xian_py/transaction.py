import requests
import json

from xian_py.wallet import Wallet
from xian_py.utils import decode_dict, decode_str
from xian_py.formating import format_dictionary, check_format_of_payload
from xian_py.exception import XianException
from xian_py.encoding import encode


def get_nonce(node_url: str, address: str) -> int:
    """
    Return next nonce for given address
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param address: Wallet address for which the nonce will be returned
    :return: Next unused nonce
    """
    try:
        r = requests.post(f'{node_url}/abci_query?path="/get_next_nonce/{address}"')
        r.raise_for_status()
    except Exception as e:
        raise XianException(e)

    data = r.json()['result']['response']['value']

    # Data is None
    if data == 'AA==':
        return 0

    nonce = decode_str(data)
    return int(nonce)


def get_tx(node_url: str, tx_hash: str, decode: bool = True) -> dict:
    """
    Return transaction either with encoded or decoded content
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param tx_hash: Hash of transaction that gets retrieved
    :param decode: If TRUE, returned JSON data will be decoded
    :return: Transaction data in JSON
    """
    try:
        r = requests.get(f'{node_url}/tx?hash=0x{tx_hash}')
    except Exception as e:
        raise XianException(e)

    data = r.json()

    if decode and 'result' in data:
        decoded = decode_dict(data['result']['tx'])
        data['result']['tx'] = decoded

        if data['result']['tx_result']['data'] is not None:
            decoded = decode_str(data['result']['tx_result']['data'])
            data['result']['tx_result']['data'] = json.loads(decoded)

    return data


def simulate_tx(node_url: str, payload: dict) -> dict:
    """ Estimate the amount of stamps a tx will cost """
    encoded = json.dumps(payload).encode().hex()

    try:
        r = requests.post(f'{node_url}/abci_query?path="/simulate_tx/{encoded}"')
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        raise XianException(e)

    res = data['result']['response']

    if res['code'] != 0:
        raise XianException(res['log'])

    return json.loads(decode_str(res['value']))


def create_tx(payload: dict, wallet: Wallet) -> dict:
    """
    Create offline transaction that can be broadcast
    :param payload: Transaction payload with following keys:
        chain_id: Network ID
        contract: Contract name to be executed
        function: Function name to be executed
        kwargs: Arguments for function
        nonce: Unique continuous number
        sender: Wallet address of sender
        stamps: Max amount of stamps to use
    :param wallet: Wallet object with public and private key
    :return: Encoded transaction data
    """
    payload = format_dictionary(payload)
    assert check_format_of_payload(payload), "Invalid payload provided!"

    tx = {
        "payload": payload,
        "metadata": {
            "signature": wallet.sign_msg(json.dumps(payload))
        }
    }

    tx = encode(format_dictionary(tx))
    return json.loads(tx)


def broadcast_tx_commit(node_url: str, tx: dict) -> dict:
    """
    DO NOT USE IN PRODUCTION - ONLY FOR TESTS IN DEVELOPMENT!
    Submits a transaction to be included in the blockchain and
    returns the response from CheckTx and DeliverTx.
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param tx: Transaction data in JSON format (dict)
    :return: JSON data with tx hash, CheckTx and DeliverTx results
    """
    payload = json.dumps(tx).encode().hex()

    try:
        r = requests.post(f'{node_url}/broadcast_tx_commit?tx="{payload}"')
    except Exception as e:
        raise XianException(e)

    data = r.json()
    return data


def broadcast_tx_sync(node_url: str, tx: dict) -> dict:
    """
    Submits a transaction to be included in the blockchain and returns
    the response from CheckTx. Does not wait for DeliverTx result.
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param tx: Transaction data in JSON format (dict)
    :return: JSON data with tx hash and CheckTx result
    """
    payload = json.dumps(tx).encode().hex()

    try:
        r = requests.post(f'{node_url}/broadcast_tx_sync?tx="{payload}"')
    except Exception as e:
        raise XianException(e)

    data = r.json()
    return data


def broadcast_tx_async(node_url: str, tx: dict):
    """
    Submits a transaction to be included in the blockchain and returns
    immediately. Does not wait for CheckTx or DeliverTx results.
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param tx: Transaction data in JSON format (dict)
    """
    payload = json.dumps(tx).encode().hex()

    try:
        requests.post(f'{node_url}/broadcast_tx_async?tx="{payload}"')
    except Exception as e:
        raise XianException(e)
