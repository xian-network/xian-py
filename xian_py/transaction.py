import aiohttp
import json

from xian_py.wallet import Wallet
from xian_py.encoding import encode, decode_dict, decode_str
from xian_py.formating import format_dictionary, check_format_of_payload
from xian_py.exception import XianException
from xian_py.async_utils import sync_wrapper


async def get_nonce_async(node_url: str, address: str) -> int:
    """
    Return next nonce for given address
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param address: Wallet address for which the nonce will be returned
    :return: Next unused nonce
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{node_url}/abci_query?path="/get_next_nonce/{address}"') as r:
                r.raise_for_status()
                data = await r.json()
    except Exception as e:
        raise XianException(e)

    value = data['result']['response']['value']

    # Data is None
    if value == 'AA==':
        return 0

    nonce = decode_str(value)
    return int(nonce)


# Sync wrapper for backward compatibility
get_nonce = sync_wrapper(get_nonce_async)


async def get_tx_async(node_url: str, tx_hash: str, decode: bool = True) -> dict:
    """
    Return transaction either with encoded or decoded content
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param tx_hash: Hash of transaction that gets retrieved
    :param decode: If TRUE, returned JSON data will be decoded
    :return: Transaction data in JSON
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{node_url}/tx?hash=0x{tx_hash}') as r:
                data = await r.json()
    except Exception as e:
        raise XianException(e)

    if decode and 'result' in data:
        decoded = decode_dict(data['result']['tx'])
        data['result']['tx'] = decoded

        if data['result']['tx_result']['data'] is not None:
            decoded = decode_str(data['result']['tx_result']['data'])
            data['result']['tx_result']['data'] = json.loads(decoded)

    return data


# Sync wrapper for backward compatibility
get_tx = sync_wrapper(get_tx_async)


async def simulate_tx_async(node_url: str, payload: dict) -> dict:
    """ Estimate the amount of stamps a tx will cost """
    encoded = json.dumps(payload).encode().hex()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{node_url}/abci_query?path="/simulate_tx/{encoded}"') as r:
                r.raise_for_status()
                data = await r.json()
    except Exception as e:
        raise XianException(e)

    res = data['result']['response']

    if res['code'] != 0:
        raise XianException(res['log'])

    return json.loads(decode_str(res['value']))


# Sync wrapper for backward compatibility
simulate_tx = sync_wrapper(simulate_tx_async)


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


async def broadcast_tx_commit_async(node_url: str, tx: dict) -> dict:
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
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{node_url}/broadcast_tx_commit?tx="{payload}"') as r:
                data = await r.json()
    except Exception as e:
        raise XianException(e)

    return data


# Sync wrapper for backward compatibility
broadcast_tx_commit = sync_wrapper(broadcast_tx_commit_async)


async def broadcast_tx_sync_async(node_url: str, tx: dict) -> dict:
    """
    Submits a transaction to be included in the blockchain and returns
    the response from CheckTx. Does not wait for DeliverTx result.
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param tx: Transaction data in JSON format (dict)
    :return: JSON data with tx hash and CheckTx result
    """
    payload = json.dumps(tx).encode().hex()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{node_url}/broadcast_tx_sync?tx="{payload}"') as r:
                data = await r.json()
    except Exception as e:
        raise XianException(e)

    return data


# Sync wrapper for backward compatibility
broadcast_tx_sync = sync_wrapper(broadcast_tx_sync_async)


async def broadcast_tx_async_async(node_url: str, tx: dict):
    """
    Submits a transaction to be included in the blockchain and returns
    immediately. Does not wait for CheckTx or DeliverTx results.
    :param node_url: Node URL in format 'http://<IP>:<Port>'
    :param tx: Transaction data in JSON format (dict)
    """
    payload = json.dumps(tx).encode().hex()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{node_url}/broadcast_tx_async?tx="{payload}"') as r:
                # Just ensure the request was sent successfully
                r.raise_for_status()
    except Exception as e:
        raise XianException(e)


# Sync wrapper for backward compatibility
broadcast_tx_async = sync_wrapper(broadcast_tx_async_async)
