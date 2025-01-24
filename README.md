# xian-py

Python SDK for interacting with the Xian blockchain network. This library provides comprehensive tools for wallet management, transaction handling, and smart contract interactions.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Usage Guide](#usage-guide)
  - [Wallet Management](#wallet-management)
  - [HD Wallet Operations](#hd-wallet-operations)
  - [Blockchain Interactions](#blockchain-interactions)
  - [Smart Contract Operations](#smart-contract-operations)
  - [Transaction Management](#transaction-management)
  - [Simulated Transactions](#simulated-transactions)
  - [Cryptography Utilities](#cryptography-utilities)

## Installation

Basic installation:
```bash
pip install xian-py
```

With Ethereum support:
```bash
pip install "xian-py[eth]"
```

## Features

- Basic and HD wallet creation and management using Ed25519 cryptography
- Optional Ethereum address generation from the same HD wallet seed
- BIP39 mnemonic seed generation and recovery (24 words)
- BIP32/SLIP-0010 compliant hierarchical deterministic wallets
- Message signing and verification
- Two-way message encryption and decryption between sender/receiver
- Transaction creation, simulation, and broadcasting
- Smart contract deployment, interaction, and validation
- Token transfers and balance queries
- Asynchronous and synchronous transaction submission
- Read-only contract execution through transaction simulation

## Usage Guide

### Wallet Management

The SDK provides two types of wallets: basic `Wallet` and hierarchical deterministic `HDWallet`.

#### Basic Wallet Operations

```python
from xian_py.wallet import Wallet

# Create new wallet with random seed
wallet = Wallet()

# Create from existing private key
wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')

# Access wallet details
print(f'Public Key: {wallet.public_key}')
print(f'Private Key: {wallet.private_key}')
```

#### HD Wallet Operations

The HD wallet implementation follows BIP39, BIP32, and SLIP-0010 standards. It can generate both Ed25519 keys for Xian and Secp256k1 keys for Ethereum from the same seed.

```python
from xian_py.wallet import HDWallet

# Create new HD wallet with 24-word mnemonic
hd_wallet = HDWallet()
print(f'Mnemonic: {hd_wallet.mnemonic_str}')

# Create from existing mnemonic
mnemonic = 'dynamic kitchen omit dinosaur found trend video morning oppose staff bid honey...'
hd_wallet = HDWallet(mnemonic)

# Derive Xian wallet
path = [44, 0, 0, 0, 0]  # m/44'/0'/0'/0'/0'
xian_wallet = hd_wallet.get_wallet(path)
print(f'Xian Address: {xian_wallet.public_key}')

# Derive Ethereum wallet (requires ethereum extras)
eth_wallet = hd_wallet.get_ethereum_wallet(0)  # Uses standard Ethereum derivation path
print(f'Ethereum Address: {eth_wallet.public_key}')

# Get multiple Ethereum accounts
eth_wallet2 = hd_wallet.get_ethereum_wallet(1)  # Second account
print(f'Second Ethereum Address: {eth_wallet2.public_key}')
```

### Blockchain Interactions

#### Token Operations

```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

# Initialize client
wallet = Wallet()
xian = Xian('http://node-ip:26657', wallet=wallet)

# Check balance
balance = xian.get_balance('address')

# Send tokens with automatic stamp calculation
result = xian.send(amount=10, to_address='recipient_address')

# Check custom token balance
token_balance = xian.get_balance('contract_address', contract='token_contract')
```

### Smart Contract Operations

#### Contract Deployment and Interaction

```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

# Initialize client
wallet = Wallet()
xian = Xian('http://node-ip:26657', wallet=wallet)

# Deploy contract
code = '''
@export
def greet(name: str):
    return f"Hello, {name}!"
'''
result = xian.submit_contract('greeting_contract', code)

# Get contract state
state = xian.get_state('contract_name', 'variable_name', 'key')

# Get and decompile contract source
source = xian.get_contract('contract_name', clean=True)
```

#### Contract Validation

The SDK supports validating smart contracts against different [contract standards](https://github.com/xian-network/xian-standard-contracts):

```python
from xian_py.validator import validate_contract, XianStandard

# Validate contract against XSC001 standard
code = '''
@construct
def seed():
    balances = Hash()
    metadata = Hash()
    metadata['token_name'] = 'MyToken'
    metadata['token_symbol'] = 'MTK'
    metadata['token_logo_url'] = 'https://example.com/logo.png'
    metadata['token_website'] = 'https://example.com'
    metadata['operator'] = ctx.caller

@export
def transfer(amount: int, to: str):
    # Transfer implementation
    pass
# ... rest of the contract code
'''

# Validate against XSC001 (default)
is_valid, errors = validate_contract(code)

# Validate against a specific standard
is_valid, errors = validate_contract(code, standard=XianStandard.XSC001)

if not is_valid:
    print("Validation errors:", errors)
```

### Transaction Management

#### High-Level Transaction

```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

wallet = Wallet()
xian = Xian('http://node-ip:26657', wallet=wallet)

result = xian.send_tx(
    contract='currency',
    function='transfer',
    kwargs={
        'to': 'recipient',
        'amount': 1000,
    }
)
```

### Simulated Transactions

The SDK supports transaction simulation for two primary purposes:
1. Estimating stamp costs before broadcasting a transaction
2. Executing read-only contract functions without spending stamps

#### Low-Level Transaction with Transaction Cost Estimation

```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian
from xian_py.transaction import get_nonce, create_tx, simulate_tx, broadcast_tx_sync

# Initialize wallet and client
wallet = Wallet()
node_url = 'http://node-ip:26657'
xian = Xian(node_url, wallet=wallet)

# Prepare transaction payload
payload = {
    "chain_id": xian.get_chain_id(),
    "contract": "currency",
    "function": "transfer",
    "kwargs": {"to": "recipient", "amount": 100},
    "nonce": get_nonce(node_url, wallet.public_key),
    "sender": wallet.public_key,
    "stamps_supplied": 0
}

# Simulate to get stamp cost
simulated = simulate_tx(node_url, payload)
print(f"Required stamps: {simulated['stamps_used']}")

# Use the simulated stamps in the actual transaction
payload['stamps_supplied'] = simulated['stamps_used']

# Create and broadcast transaction
tx = create_tx(payload, wallet)
result = broadcast_tx_sync(node_url, tx)
```

#### Read-Only Contract Execution

You can execute read-only contract functions without spending stamps by using transaction simulation. This is useful for querying contract state or calculating values without modifying the blockchain.

In the payload for a simulated transaction you don't need to specify the following keys:
- stamps_supplied
- chain_id
- nonce

```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian
from xian_py.transaction import simulate_tx

# Initialize client
wallet = Wallet()
node_url = 'http://node-ip:26657'
xian = Xian(node_url, wallet=wallet)

# Prepare read-only query payload
payload = {
    "contract": "token_contract",
    "function": "get_balance",
    "kwargs": {"address": wallet.public_key},
    "sender": wallet.public_key,
}

# Execute simulation and get result
result = simulate_tx(node_url, payload)
print(f"Balance: {result['result']}")
```

### Cryptography Utilities

The SDK provides comprehensive cryptographic utilities for message signing, verification, and secure communication between parties.

#### Message Signing and Verification

The SDK supports message signing and verification for both Xian and Ethereum wallets.

```python
from xian_py.wallet import Wallet, HDWallet, EthereumWallet

# Create wallets 
xian_wallet = Wallet()
hd_wallet = HDWallet()
eth_wallet = hd_wallet.get_ethereum_wallet(0)

# Sign and verify with Xian wallet
message = "Important message to verify"
xian_signature = xian_wallet.sign_msg(message)
print(f'Xian signature valid: {xian_wallet.verify_msg(message, xian_signature)}')

# Sign and verify with Ethereum wallet
eth_signature = eth_wallet.sign_msg(message)
print(f'Ethereum signature valid: {eth_wallet.verify_msg(message, eth_signature)}')

# Validate key formats
print(f'Xian key valid: {Wallet.is_valid_key(xian_wallet.public_key)}')
print(f'Ethereum address valid: {EthereumWallet.is_valid_key(eth_wallet.public_key)}')
```

#### Two-Way Message Encryption

Messages can be encrypted using the sender's private key and recipient's public key. The encrypted message can then be decrypted by either party using their respective keys.

```python
from xian_py.wallet import Wallet
from xian_py.crypto import encrypt, decrypt_as_sender, decrypt_as_receiver

# Create sender and receiver wallets
sender_wallet = Wallet()
receiver_wallet = Wallet()

# Encrypt message
message = "Secret message"
encrypted = encrypt(
    sender_wallet.private_key,
    receiver_wallet.public_key,
    message
)

# Decrypt as sender
decrypted_sender = decrypt_as_sender(
    sender_wallet.private_key,
    receiver_wallet.public_key,
    encrypted
)

# Decrypt as receiver
decrypted_receiver = decrypt_as_receiver(
    sender_wallet.public_key,
    receiver_wallet.private_key,
    encrypted
)

# Both parties get the original message
assert message == decrypted_sender == decrypted_receiver
print("Message successfully encrypted and decrypted by both parties!")
```