import requests
import json

from xian_py.wallet import Wallet
from xian_py.utils import decode_dict, decode_str
from xian_py.formating import format_dictionary, check_format_of_payload
from xian_py.exception import XianException
from xian_py.encoding import encode

from typing import Dict, Any


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


def get_tx(node_url: str, tx_hash: str, decode: bool = True) -> Dict[str, Any]:
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


def estimate_stamps(node_url: str, tx: Dict[str, Any]) -> int:
    """ Estimate the amount of stamps a tx will cost """
    payload = json.dumps(tx).encode().hex()

    try:
        r = requests.post(f'{node_url}/abci_query?path="/estimate_stamps/{payload}"')
        r.raise_for_status()
    except Exception as e:
        raise XianException(e)

    data = r.json()['result']['response']['value']
    decoded_json = json.loads(decode_str(data))
    stamps = decoded_json['stamps_used']

    return int(stamps)


def create_tx(
        contract: str,
        function: str,
        kwargs: Dict[str, Any],
        stamps: int,
        chain_id: str,
        private_key: str,
        nonce: int) -> Dict[str, Any]:
    """
    Create offline transaction that can be broadcast
    :param contract: Contract name to be executed
    :param function: Function name to be executed
    :param kwargs: Arguments for function
    :param stamps: Max amount of stamps to use
    :param chain_id: Network ID
    :param private_key: Private key to sign with
    :param nonce: Unique continuous number
    :return: Encoded transaction data
    """
    wallet = Wallet(private_key)

    payload = {
        "chain_id": chain_id,
        "contract": contract,
        "function": function,
        "kwargs": kwargs,
        "nonce": nonce,
        "sender": wallet.public_key,
        "stamps_supplied": stamps
    }

    payload = format_dictionary(payload)
    assert check_format_of_payload(payload), "Invalid payload provided!"

    tx = {
        "payload": payload,
        "metadata": {
            "signature": wallet.sign_msg(encode(payload))
        }
    }

    tx = encode(format_dictionary(tx))
    return json.loads(tx)


def broadcast_tx_commit(node_url: str, tx: Dict[str, Any]) -> Dict[str, Any]:
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


def broadcast_tx_sync(node_url: str, tx: Dict[str, Any]) -> Dict[str, Any]:
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


def broadcast_tx_async(node_url: str, tx: Dict[str, Any]):
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
