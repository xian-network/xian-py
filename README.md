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

Replace `some-chain-id` with the chain ID of the network that you want to connect to. A chain ID is an ID that ensures that transactions can only be used in the network for which they were originally generated.

Official chain IDs for Xian can be found [here](https://github.com/XianChain/xian/wiki#chain-ids)

### Submit contract
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', 'some-chain-id', wallet)

# Contract code
code = '''
token_name = Variable() # Optional

@construct
def seed():
    # Create a token with the information from fixtures/tokenInfo
    token_name.set("Test Token")

@export
def set_token_name(new_name: str):
    # Set the token name
    token_name.set(new_name)
'''

# Deploy contract on network
submit = xian.submit_contract('con_new_token', code)

print(f'success: {submit["success"]}')
print(f'tx_hash: {submit["tx_hash"]}')
```

### Approve contract and retrieve approved amount
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', 'some-chain-id', wallet)

# Get approved amount
approved = xian.get_approved_amount('con_new_token')
print(f'approved: {approved}')

# Approve the default amount
approve = xian.approve('con_new_token')
print(f'success: {approve["success"]}')
print(f'tx_hash: {approve["tx_hash"]}')

# Get approved amount again
approved = xian.get_approved_amount('con_new_token')
print(f'approved: {approved}')
```

### Get token balance for an address
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', 'some-chain-id', wallet)

balance = xian.get_balance('con_new_token')
print(f'balance: {balance}')
```

# Transactions

### Send a transaction - High level usage
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', 'some-chain-id', wallet)

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
```python
from xian_py.wallet import Wallet
from xian_py.transactions import get_nonce, create_tx, broadcast_tx

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

data = broadcast_tx(node_url, tx)
print(f'success: {data["success"]}')
print(f'tx_hash: {data["tx_hash"]}')
```

### Retrieve transaction by hash
```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')
xian = Xian('http://<node IP>:26657', 'some-chain-id', wallet)

tx = xian.get_tx('some tx hash')
print(f'transaction: {tx}')
```

