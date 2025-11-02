import asyncio
from typing import Optional

from xian_py.xian_async import XianAsync
from xian_py.wallet import Wallet


class Xian:
    """Synchronous wrapper around XianAsync for backward compatibility"""
    
    def __init__(self, node_url: str, chain_id: str = None, wallet: Wallet = None):
        self.node_url = node_url
        self.wallet = wallet if wallet else Wallet()
        self._async_client = XianAsync(node_url, chain_id, self.wallet)
        
        # Initialize chain_id synchronously if not provided
        if chain_id is None:
            self.chain_id = self.get_chain_id()
            self._async_client.chain_id = self.chain_id
            self._async_client._chain_id_set = True
        else:
            self.chain_id = chain_id

    def _run_async(self, coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._run_with_cleanup(coro))
        raise RuntimeError(
            "Cannot call sync methods from within an async context. "
            "Use XianAsync directly for async operations."
        )

    async def _run_with_cleanup(self, coro):
        try:
            return await coro
        finally:
            await self._async_client.close()

    def get_tx(self, tx_hash: str) -> dict:
        """ Return transaction data """
        return self._run_async(self._async_client.get_tx(tx_hash))

    def get_balance(self, address: str = None, contract: str = 'currency') -> int | float:
        return self._run_async(self._async_client.get_balance(address, contract))

    def send_tx(
            self,
            contract: str,
            function: str,
            kwargs: dict,
            stamps: int = 0,
            nonce: int = None,
            chain_id: str = None,
            synchronous: bool = True) -> Optional[dict]:
        """ Send a transaction to the network """
        return self._run_async(self._async_client.send_tx(
            contract, function, kwargs, stamps, nonce, chain_id, synchronous
        ))

    def send(
            self,
            amount: int | float | str,
            to_address: str,
            token: str = "currency",
            stamps: int = 0) -> dict:
        """ Send a token to a given address """
        return self._run_async(self._async_client.send(amount, to_address, token, stamps))

    def simulate(self, contract: str, function: str, kwargs: dict) -> dict:
        return self._run_async(self._async_client.simulate(contract, function, kwargs))

    def get_state(
            self,
            contract: str,
            variable: str,
            *keys: str) -> None | int | float | dict | str:
        """ Retrieve contract state and decode it """
        return self._run_async(self._async_client.get_state(contract, variable, *keys))

    def get_contract(
            self,
            contract: str,
            clean: bool = False) -> None | str:
        """ Retrieve contract and decode it """
        return self._run_async(self._async_client.get_contract(contract, clean))

    def get_approved_amount(
            self,
            contract: str,
            address: str = None,
            token: str = 'currency') -> int | float:
        """ Retrieve approved token amount for a contract """
        return self._run_async(self._async_client.get_approved_amount(contract, address, token))

    def approve(
            self,
            contract: str,
            token: str = "currency",
            amount: int | float | str = 999999999999) -> dict:
        """ Approve smart contract to spend max token amount """
        return self._run_async(self._async_client.approve(contract, token, amount))

    def submit_contract(
            self,
            name: str,
            code: str,
            args: dict = None,
            stamps: int = 0) -> dict:
        """ Submit a contract to the network """
        return self._run_async(self._async_client.submit_contract(name, code, args, stamps))

    def get_nodes(self) -> list:
        """ Retrieve list of nodes from the network """
        return self._run_async(self._async_client.get_nodes())

    def get_genesis(self):
        """ Retrieve genesis info from the network """
        return self._run_async(self._async_client.get_genesis())

    def get_chain_id(self):
        """ Retrieve chain_id from the network """
        return self._run_async(self._async_client.get_chain_id())
