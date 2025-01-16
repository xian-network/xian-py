# xian-py

Python SDK for interacting with the Xian blockchain network. This library provides comprehensive tools for wallet management, transaction handling, and smart contract interactions.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
  - [Wallet Management](#wallet-management)
  - [HD Wallet Operations](#hd-wallet-operations)
  - [Blockchain Interactions](#blockchain-interactions)
  - [Smart Contract Operations](#smart-contract-operations)
  - [Transaction Management](#transaction-management)
  - [Simulated Transactions](#simulated-transactions)
  - [Cryptography Utilities](#cryptography-utilities)

## Installation

```bash
pip install xian-py
```

## Features

- Basic and HD wallet creation and management using Ed25519 cryptography
- BIP39 mnemonic seed generation and recovery (24 words)
- BIP32/SLIP-0010 compliant hierarchical deterministic wallets
- Message signing and verification
- Two-way message encryption and decryption between sender/receiver
- Transaction creation, simulation, and broadcasting
- Smart contract deployment and interaction
- Token transfers and balance queries
- Asynchronous and synchronous transaction submission
- Read-only contract execution through transaction simulation

## Quick Start

```python
from xian_py.wallet import Wallet
from xian_py.xian import Xian

# Create a new wallet
wallet = Wallet()
print(f"Address: {wallet.public_key}")

# Initialize Xian client
xian = Xian('http://your-node-ip:26657', wallet=wallet)

# Send XIAN tokens
result = xian.send(
    amount=7,
    to_address='b6504cf056e264a4c1932d5de6893d110db5459ab4f742eb415d98ed989bb988'
)
```

## Usage Guide

### Wallet Management

The SDK provides two types of wallets: basic `Wallet` and hierarchical deterministic `HDWallet`.

#### Basic Wallet Operations

```python
from xian_py.wallet import Wallet
from xian_py.wallet import verify_msg

# Create new wallet with random seed
wallet = Wallet()

# Create from existing private key
wallet = Wallet('ed30796abc4ab47a97bfb37359f50a9c362c7b304a4b4ad1b3f5369ecb6f7fd8')

# Access wallet details
print(f'Public Key: {wallet.public_key}')
print(f'Private Key: {wallet.private_key}')
```

### HD Wallet Operations

The HD wallet implementation follows BIP39, BIP32, and SLIP-0010 standards for Ed25519 keys.

```python
from xian_py.wallet import HDWallet, Wallet

# Create new HD wallet with 24-word mnemonic
hd_wallet = HDWallet()
print(f'Mnemonic: {hd_wallet.mnemonic_str}')  # Space-separated words
print(f'Words: {hd_wallet.mnemonic_lst}')     # List of words

# Create from existing mnemonic
mnemonic = 'dynamic kitchen omit dinosaur found trend video morning oppose staff bid honey...'
hd_wallet = HDWallet(mnemonic)

# Derive child wallets (keys are automatically hardened)
path = [44, 0, 0, 0, 0]  # m/44'/0'/0'/0'/0'
wallet0 = hd_wallet.get_wallet(path)
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

#### Message Verification and Key Validation

```python
from xian_py.wallet import Wallet, verify_msg, key_is_valid

# Create a wallet to demonstrate signing and verification
wallet = Wallet()

# Sign a message
message = "Important message to verify"
signature = wallet.sign_msg(message)

# Verify message signature
is_valid = verify_msg(wallet.public_key, message, signature)
print(f'Signature valid: {is_valid}')  # Should print True

# Validate key format
is_valid_key = key_is_valid(wallet.public_key)  # Works for both public and private keys
print(f'Key valid: {is_valid_key}')  # Should print True
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