import ast
import requests

import xian_py.utils as utl
import xian_py.transaction as tr

from xian_py.exception import XianException
from xian_py.wallet import Wallet

from typing import Optional


class Xian:
    def __init__(self, node_url: str, chain_id: str = None, wallet: Wallet = None):
        self.node_url = node_url
        self.chain_id = chain_id if chain_id else self.get_chain_id()
        self.wallet = wallet if wallet else Wallet()

    def get_tx(self, tx_hash: str) -> dict:
        """ Return transaction data """

        data = tr.get_tx(self.node_url, tx_hash)

        if 'error' in data:
            data['success'] = False
            data['message'] = data['error']['data']
        elif data['result']['tx_result']['code'] == 0:
            data['success'] = True
        else:
            data['success'] = False
            data['message'] = data['result']['tx_result']['data']['result']

        return data

    def get_balance(
            self,
            address: str = None,
            contract: str = 'currency') -> int | float:
        """ Return balance for given address and token contract """

        address = address if address else self.wallet.public_key

        try:
            r = requests.get(f'{self.node_url}/abci_query?path="/get/{contract}.balances:{address}"')
        except Exception as e:
            raise XianException(e)

        json_data = r.json()
        balance_byte_string = json_data['result']['response']['value']

        # Balance is 0
        if not balance_byte_string:
            return 0
        # Decodes to 'None' --> balance is 0
        elif balance_byte_string == 'AA==':
            return 0

        balance = utl.decode_str(balance_byte_string)

        if balance.isdigit():
            balance = int(balance)
        else:
            if float(balance).is_integer():
                balance = int(float(balance))
            else:
                balance = float(balance)

        return balance

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

        if chain_id is None:
            if self.chain_id:
                chain_id = self.chain_id

        if nonce is None:
            nonce = tr.get_nonce(
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
            simulated_tx = tr.simulate_tx(
                self.node_url,
                payload
            )

            stamps = simulated_tx['stamps_used']
            payload['stamps_supplied'] = stamps

        tx = tr.create_tx(payload, self.wallet)

        if synchronous:
            data = tr.broadcast_tx_sync(self.node_url, tx)

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
            tr.broadcast_tx_async(self.node_url, tx)

    def send(
            self,
            amount: int | float | str,
            to_address: str,
            token: str = "currency",
            stamps: int = 0) -> dict:
        """ Send a token to a given address """

        return self.send_tx(
            token,
            "transfer",
            {"amount": float(amount), "to": to_address},
            stamps=stamps
        )

    def get_state(
            self,
            contract: str,
            variable: str,
            *keys: str) -> None | int | float | dict | str:
        """ Retrieve contract state and decode it """

        path = f'/get/{contract}.{variable}'

        if len(keys) > 0:
            path = f'{path}:{":".join(keys)}' if keys else path

        try:
            r = requests.get(f'{self.node_url}/abci_query?path="{path}"')
        except Exception as e:
            raise XianException(e)

        byte_string = r.json()['result']['response']['value']

        # Decodes to 'None'
        if byte_string is None or byte_string == 'AA==':
            return None

        data = utl.decode_str(byte_string)

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

    def get_contract(
            self,
            contract: str,
            clean: bool = False) -> None | str:
        """ Retrieve contract and decode it """

        try:
            r = requests.get(f'{self.node_url}/abci_query?path="contract/{contract}"')
        except Exception as e:
            raise XianException(e)

        byte_string = r.json()['result']['response']['value']

        # Decodes to 'None'
        if byte_string is None or byte_string == 'AA==':
            return None

        code = utl.decode_str(byte_string)

        if not clean: return code
        return utl.remove_trailing_double_underscores(code)

    def get_approved_amount(
            self,
            contract: str,
            address: str = None,
            token: str = 'currency') -> int | float:
        """ Retrieve approved token amount for a contract """

        address = address if address else self.wallet.public_key

        value = self.get_state(token, 'balances', address, contract)
        value = 0 if value is None else value

        return value

    def approve(
            self,
            contract: str,
            token: str = "currency",
            amount: int | float | str = 999999999999) -> dict:
        """ Approve smart contract to spend max token amount """

        return self.send_tx(
            token,
            "approve",
            {"amount": float(amount), "to": contract}
        )

    def submit_contract(
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

        return self.send_tx(
            'submission',
            'submit_contract',
            kwargs,
            stamps
        )

    def get_nodes(self) -> list:
        """ Retrieve list of nodes from the network """

        try:
            r = requests.post(f'{self.node_url}/net_info')
        except Exception as e:
            raise XianException(e)

        peers = r.json()['result']['peers']

        ips = list()

        for peer in peers:
            ips.append(peer['remote_ip'])

        return ips

    def get_genesis(self):
        """ Retrieve genesis info from the network """

        try:
            r = requests.post(f'{self.node_url}/genesis')
        except Exception as e:
            raise XianException(e)

        data = r.json()
        return data

    def get_chain_id(self):
        """ Retrieve chain_id from the network """
        chain_id = self.get_genesis()['result']['genesis']['chain_id']
        return chain_id
