import ast
import aiohttp

import xian_py.transaction as tr
from xian_py.decompiler import ContractDecompiler
from xian_py.encoding import decode_str
from xian_py.exception import XianException
from xian_py.wallet import Wallet

from typing import Optional


class XianAsync:
    """Async version of the Xian class for non-blocking operations"""
    
    def __init__(
        self,
        node_url: str,
        chain_id: str = None,
        wallet: Wallet = None,
        *,
        session: Optional[aiohttp.ClientSession] = None,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        connector: Optional[aiohttp.TCPConnector] = None,
    ):
        self.node_url = node_url.rstrip("/")
        self.chain_id = chain_id  # Will be set asynchronously if needed
        self.wallet = wallet if wallet else Wallet()
        self._chain_id_set = chain_id is not None
        self._external_session = session
        self._timeout = timeout or aiohttp.ClientTimeout(
            total=15, sock_connect=3, sock_read=10
        )
        self._connector_params = connector
        self._session: Optional[aiohttp.ClientSession] = session

    async def __aenter__(self) -> "XianAsync":
        if self._session is None:
            connector = self._connector_params or aiohttp.TCPConnector(
                limit=100, ttl_dns_cache=300
            )
            self._session = aiohttp.ClientSession(
                timeout=self._timeout, connector=connector
            )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            # lazy create for users who don't use context manager
            connector = self._connector_params or aiohttp.TCPConnector(
                limit=100, ttl_dns_cache=300
            )
            self._session = aiohttp.ClientSession(
                timeout=self._timeout, connector=connector
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._external_session:
            await self._session.close()
        self._session = None

    async def ensure_chain_id(self):
        """Ensure chain_id is set, fetching it if necessary"""
        if not self._chain_id_set:
            self.chain_id = await self.get_chain_id()
            self._chain_id_set = True

    async def get_tx(self, tx_hash: str) -> dict:
        """ Return transaction data """

        data = await tr.get_tx_async(self.node_url, tx_hash)

        if 'error' in data:
            data['success'] = False
            data['message'] = data['error']['data']
        elif data['result']['tx_result']['code'] == 0:
            data['success'] = True
        else:
            data['success'] = False
            data['message'] = data['result']['tx_result']['data']['result']

        return data

    async def get_balance(self, address: str = None, contract: str = 'currency') -> int | float:
        address = address or self.wallet.public_key

        async def query_simulate():
            payload = {
                "contract": contract,
                "function": "balance_of",
                "kwargs": {"address": address},
                "sender": self.wallet.public_key
            }
            data = await tr.simulate_tx_async(self.node_url, payload)
            return data['result']

        async def query_abci():
            async with self.session.get(f'{self.node_url}/abci_query?path="/get/{contract}.balances:{address}"') as r:
                response = await r.json()
                balance_bytes = response['result']['response']['value']

                if not balance_bytes or balance_bytes == 'AA==':
                    return '0'

                return decode_str(balance_bytes)

        def normalize_balance(balance: str) -> int | float:
            if balance.isdigit():
                return int(balance)
            num = float(balance)
            return int(num) if num.is_integer() else num

        try:
            return normalize_balance(await query_simulate())
        except:
            try:
                return normalize_balance(await query_abci())
            except Exception as e:
                raise XianException(e)

    async def send_tx(
            self,
            contract: str,
            function: str,
            kwargs: dict,
            stamps: int = 0,
            nonce: int = None,
            chain_id: str = None,
            synchronous: bool = True) -> Optional[dict]:
        """ Send a transaction to the network """

        if chain_id is None:
            await self.ensure_chain_id()
            chain_id = self.chain_id

        if nonce is None:
            nonce = await tr.get_nonce_async(
                self.node_url,
                self.wallet.public_key
            )

        payload = {
            "chain_id": chain_id,
            "contract": contract,
            "function": function,
            "kwargs": kwargs,
            "nonce": nonce,
            "sender": self.wallet.public_key,
            "stamps_supplied": stamps
        }

        if stamps == 0:
            simulated_tx = await tr.simulate_tx_async(
                self.node_url,
                payload
            )

            stamps = simulated_tx['stamps_used']
            payload['stamps_supplied'] = stamps

        tx = tr.create_tx(payload, self.wallet)

        if synchronous:
            data = await tr.broadcast_tx_sync_async(self.node_url, tx)

            result = {
                'success': None,
                'message': None,
                'tx_hash': None,
                'response': data
            }

            if 'error' in data:
                result['success'] = False
                result['message'] = data['error']['data']
            elif data['result']['code'] == 0:
                result['success'] = True
                result['tx_hash'] = data['result']['hash']
            else:
                result['success'] = False
                result['message'] = data['result']['log']
                result['tx_hash'] = data['result']['hash']

            return result

        else:
            await tr.broadcast_tx_async_async(self.node_url, tx)

    async def send(
            self,
            amount: int | float | str,
            to_address: str,
            token: str = "currency",
            stamps: int = 0) -> dict:
        """ Send a token to a given address """

        return await self.send_tx(
            token,
            "transfer",
            {"amount": float(amount), "to": to_address},
            stamps=stamps
        )

    async def simulate(self, contract: str, function: str, kwargs: dict) -> dict:
        payload = {
            "contract": contract,
            "function": function,
            "kwargs": kwargs,
            "sender": self.wallet.public_key
        }
        return await tr.simulate_tx_async(self.node_url, payload)

    async def get_state(
            self,
            contract: str,
            variable: str,
            *keys: str) -> None | int | float | dict | str:
        """ Retrieve contract state and decode it """

        path = f'/get/{contract}.{variable}'

        if len(keys) > 0:
            path = f'{path}:{":".join(keys)}' if keys else path

        try:
            async with self.session.get(f'{self.node_url}/abci_query?path="{path}"') as r:
                response = await r.json()
        except Exception as e:
            raise XianException(e)

        byte_string = response['result']['response']['value']

        # Decodes to 'None'
        if byte_string is None or byte_string == 'AA==':
            return None

        data = decode_str(byte_string)

        try:
            return int(data)
        except:
            pass
        try:
            if float(data).is_integer():
                return int(float(data))
            return float(data)
        except:
            pass
        try:
            return ast.literal_eval(data)
        except:
            pass

        return data

    async def get_contract(
            self,
            contract: str,
            clean: bool = False) -> None | str:
        """ Retrieve contract and decode it """

        try:
            async with self.session.get(f'{self.node_url}/abci_query?path="contract/{contract}"') as r:
                response = await r.json()
        except Exception as e:
            raise XianException(e)

        byte_string = response['result']['response']['value']

        # Decodes to 'None'
        if byte_string is None or byte_string == 'AA==':
            return None

        code = decode_str(byte_string)

        if clean:
            return ContractDecompiler().decompile(code)
        else:
            return code

    async def get_approved_amount(
            self,
            contract: str,
            address: str = None,
            token: str = 'currency') -> int | float:
        """ Retrieve approved token amount for a contract """

        address = address if address else self.wallet.public_key

        value = await self.get_state(token, 'approvals', address, contract)

        if value is None:
            # For backward compatibility when approvals are stored in balances
            value = await self.get_state(token, 'balances', address, contract)

        value = 0 if value is None else value

        return value

    async def approve(
            self,
            contract: str,
            token: str = "currency",
            amount: int | float | str = 999999999999) -> dict:
        """ Approve smart contract to spend max token amount """

        return await self.send_tx(
            token,
            "approve",
            {"amount": float(amount), "to": contract}
        )

    async def submit_contract(
            self,
            name: str,
            code: str,
            args: dict = None,
            stamps: int = 0) -> dict:
        """ Submit a contract to the network """

        kwargs = dict()
        kwargs['name'] = name
        kwargs['code'] = code

        if args:
            kwargs['constructor_args'] = args

        return await self.send_tx(
            'submission',
            'submit_contract',
            kwargs,
            stamps
        )

    async def get_nodes(self) -> list:
        """ Retrieve list of nodes from the network """

        try:
            async with self.session.post(f'{self.node_url}/net_info') as r:
                response = await r.json()
        except Exception as e:
            raise XianException(e)

        peers = response['result']['peers']

        ips = list()

        for peer in peers:
            ips.append(peer['remote_ip'])

        return ips

    async def get_genesis(self):
        """ Retrieve genesis info from the network """

        try:
            async with self.session.post(f'{self.node_url}/genesis') as r:
                data = await r.json()
        except Exception as e:
            raise XianException(e)

        return data

    async def get_chain_id(self):
        """ Retrieve chain_id from the network """
        genesis = await self.get_genesis()
        chain_id = genesis['result']['genesis']['chain_id']
        return chain_id