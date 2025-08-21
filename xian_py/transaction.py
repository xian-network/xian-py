"""
Transaction and network helper functions for interacting with a Xian node.

These helpers have been refactored to use `aiohttp` for all HTTP I/O.
Each function has a true asynchronous implementation (prefixed with `_`)
and a synchronous wrapper that executes the coroutine using `run_sync`.
Consumers that wish to leverage asyncio for concurrency should prefer the
async functions; legacy synchronous callers can continue to use the
original names, which now delegate to their async counterparts via run_sync.
"""

import json
from typing import Any, Dict

import aiohttp

from xian_py.wallet import Wallet
from xian_py.encoding import encode, decode_dict, decode_str
from xian_py.formating import format_dictionary, check_format_of_payload
from xian_py.exception import XianException
from xian_py.run_sync import run_sync


async def _get_nonce(node_url: str, address: str) -> int:
    """Asynchronously retrieve the next nonce for the given address."""
    url = f"{node_url}/abci_query?path=\"/get_next_nonce/{address}\""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                resp_data = await resp.json()
    except Exception as e:
        raise XianException(e)

    data = resp_data['result']['response']['value']
    if data == 'AA==':
        return 0
    nonce = decode_str(data)
    return int(nonce)


def get_nonce(node_url: str, address: str) -> int:
    """Synchronous wrapper for _get_nonce."""
    return run_sync(_get_nonce(node_url, address))


async def _get_tx(node_url: str, tx_hash: str, decode: bool = True) -> Dict[str, Any]:
    """Asynchronously return transaction details, optionally decoding content."""
    url = f"{node_url}/tx?hash=0x{tx_hash}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
    except Exception as e:
        raise XianException(e)

    if decode and 'result' in data:
        decoded_tx = decode_dict(data['result']['tx'])
        data['result']['tx'] = decoded_tx

        tx_data = data['result']['tx_result'].get('data')
        if tx_data is not None:
            decoded = decode_str(tx_data)
            data['result']['tx_result']['data'] = json.loads(decoded)
    return data


def get_tx(node_url: str, tx_hash: str, decode: bool = True) -> Dict[str, Any]:
    """Synchronous wrapper for _get_tx."""
    return run_sync(_get_tx(node_url, tx_hash, decode))


async def _simulate_tx(node_url: str, payload: dict) -> Dict[str, Any]:
    """Asynchronously estimate the amount of stamps a tx will cost."""
    encoded = json.dumps(payload).encode().hex()
    url = f"{node_url}/abci_query?path=\"/simulate_tx/{encoded}\""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                data = await resp.json()
    except Exception as e:
        raise XianException(e)

    res = data['result']['response']
    if res['code'] != 0:
        raise XianException(res['log'])
    return json.loads(decode_str(res['value']))


def simulate_tx(node_url: str, payload: dict) -> Dict[str, Any]:
    """Synchronous wrapper for _simulate_tx."""
    return run_sync(_simulate_tx(node_url, payload))


def create_tx(payload: dict, wallet: Wallet) -> dict:
    """
    Create offline transaction that can be broadcast.

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


async def _broadcast_tx_commit(node_url: str, tx: dict) -> Dict[str, Any]:
    """Asynchronously submit a transaction and wait for CheckTx and DeliverTx."""
    payload_hex = json.dumps(tx).encode().hex()
    url = f"{node_url}/broadcast_tx_commit?tx=\"{payload_hex}\""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                data = await resp.json()
    except Exception as e:
        raise XianException(e)
    return data


def broadcast_tx_commit(node_url: str, tx: dict) -> Dict[str, Any]:
    """Synchronous wrapper for _broadcast_tx_commit."""
    return run_sync(_broadcast_tx_commit(node_url, tx))


async def _broadcast_tx_sync(node_url: str, tx: dict) -> Dict[str, Any]:
    """Asynchronously submit a transaction and wait for CheckTx."""
    payload_hex = json.dumps(tx).encode().hex()
    url = f"{node_url}/broadcast_tx_sync?tx=\"{payload_hex}\""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url) as resp:
                data = await resp.json()
    except Exception as e:
        raise XianException(e)
    return data


def broadcast_tx_sync(node_url: str, tx: dict) -> Dict[str, Any]:
    """Synchronous wrapper for _broadcast_tx_sync."""
    return run_sync(_broadcast_tx_sync(node_url, tx))


async def _broadcast_tx_async(node_url: str, tx: dict) -> None:
    """Asynchronously submit a transaction without waiting for any result."""
    payload_hex = json.dumps(tx).encode().hex()
    url = f"{node_url}/broadcast_tx_async?tx=\"{payload_hex}\""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url):
                pass
    except Exception as e:
        raise XianException(e)


def broadcast_tx_async(node_url: str, tx: dict) -> None:
    """Synchronous wrapper for _broadcast_tx_async."""
    return run_sync(_broadcast_tx_async(node_url, tx))
