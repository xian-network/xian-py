### How to install

```python
pip install xian-py
```

# Wallet

### Create new wallet
```python
from xian_py.wallet import Wallet

# Create wallet from scratch
wallet = Wallet()
```

### Create wallet from existing private key
```python
from xian_py.wallet import Wallet

# Create wallet from existing private key
privkey = 'ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8'
wallet = Wallet(privkey)
```

### Get private key and public key
```python
from xian_py.wallet import Wallet

wallet = Wallet()

# Public key
address = wallet.public_key
print(f'address: {address}')

# Private key
privkey = wallet.private_key
print(f'private key: {privkey}')
```

### Sign message with private key
```python
from xian_py.wallet import Wallet

wallet = Wallet()

# Sign message with private key
message = 'I will sign this message'
signed = wallet.sign_msg(message)
print(f'Signed message: {signed}')
```

# Xian

### Send XIAN tokens
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

send_xian = xian.send(
    amount=7,
    to_address='b6504cf056e264a4c1932d5de6893d110db5459ab4f742eb415d98ed989bb988'
)

print(f'success: {send_xian["success"]}')
print(f'tx_hash: {send_xian["tx_hash"]}')
```

### Submit contract
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

# Contract code
code = '''
I = importlib

@export
def send(addresses: list, amount: float, contract: str):
    token = I.import_module(contract)

    for address in addresses:
        token.transfer_from(amount=amount, to=address, main_account=ctx.signer)
'''

# Deploy contract to network
submit = xian.submit_contract('con_multisend', code)

print(f'success: {submit["success"]}')
print(f'tx_hash: {submit["tx_hash"]}')
```

### Submit contract with constructor arguments
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

# Contract code
code = '''
test = Variable()

@construct
def init(test_var: str):
    test.set(test_var)

@export
def test():
    return test.get()
'''

# Constructor arguments
arguments = {
    'test_var': '12345'
}

# Deploy contract to network and pass arguments to it
submit = xian.submit_contract('con_multisend', code, args=arguments)

print(f'success: {submit["success"]}')
print(f'tx_hash: {submit["tx_hash"]}')
```

### Approve contract and retrieve approved amount
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

# Get approved amount
approved = xian.get_approved_amount('con_multisend')
print(f'approved: {approved}')

# Approve the default amount
approve = xian.approve('con_multisend')
print(f'approve success: {approve["success"]}')
print(f'approve tx_hash: {approve["tx_hash"]}')

# Get approved amount again
approved = xian.get_approved_amount('con_multisend')
print(f'approved success: {approved["success"]}')
print(f'approved tx_hash: {approved["tx_hash"]}')
```

### Get XIAN token balance of an address
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

balance = xian.get_balance('b6504cf056e264a4c1932d5de6893d110db5459ab4f742eb415d98ed989bb988')
print(f'balance: {balance}')
```

### Get custom token balance for a contract

Contracts can have token balances and in this example `con_token` is a token contract and we want to check the balance of that token in the contract `con_test_contract`

```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

balance = xian.get_balance('con_test_contract', contract='con_token')
print(f'balance: {balance}')
```

### Retrieve transaction by hash
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

# Provide tx hash to get tx result
tx = xian.get_tx('2C403B728E4AFFD656CAFAD38DD3E34C7CC8DA06464A7A5B1E8A426290F505A9')
print(f'transaction: {tx}')
```

### Retrieve state from a contract

In this case we assume that there is a token contract `con_testing` that has a variable called `balances` which is a Hash class and holds the balances

```python
from xian_py.xian import Xian

xian = Xian('http://<node IP>:26657')
tx = xian.get_state('con_testing', 'balances', '8bf21c7dc3a4ff32996bf56a665e1efe3c9261cc95bbf82552c328585c863829')
print(f'data: {tx}')
```

### Retrieve the source code of a contract

In this case we assume that there is a contract `con_testing`

```python
from xian_py.xian import Xian

xian = Xian('http://<node IP>:26657')
tx = xian.get_contract('con_testing')
print(f'data: {tx}')
```

If you want to clean the code up so that it doesn't have trailing double underscores, you can use the parameter `clean=True`

```python
from xian_py.xian import Xian

xian = Xian('http://<node IP>:26657')
tx = xian.get_contract('con_testing', clean=True)
print(f'data: {tx}')
```

# Transactions

### Send a transaction - High level usage
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', wallet=wallet)

send = xian.send_tx(
    contract='currency',
    function='transfer',
    kwargs={
        'to': 'burned',
        'amount': 1000,
    }
)

print(f'success: {send["success"]}')
print(f'tx_hash: {send["tx_hash"]}')
```

### Send a transaction - Low level usage

There are different ways to submit a transaction:
- `broadcast_tx_async` --> Only submit, no result will be returned
- `broadcast_tx_sync` --> Submit and return transaction validation result
- `broadcast_tx_commit` --> Submit and return result of transaction validation and processing

Do NOT use `broadcast_tx_commit` in production!

```python
from xian_py.wallet import Wallet
from xian_py.transaction import get_nonce, create_tx, broadcast_tx_sync

node_url = "http://<node IP>:26657"
wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')

next_nonce = get_nonce(node_url, wallet.public_key)
print(f'next nonce: {next_nonce}')

tx = create_tx(
    contract="currency",
    function="transfer",
    kwargs={
        "to": "burned",
        "amount": 100,
    },
    nonce=next_nonce,
    stamps=100,
    chain_id='some-chain-id',
    private_key=wallet.private_key
)
print(f'tx: {tx}')

# Return result of transaction validation
data = broadcast_tx_sync(node_url, tx)
print(f'success: {data["success"]}')
print(f'tx_hash: {data["tx_hash"]}')
```
