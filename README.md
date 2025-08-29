# xian-py

Python SDK for interacting with the Xian blockchain network. This library provides comprehensive tools for wallet management, transaction handling, and smart contract interactions with both synchronous and asynchronous support.

## Table of Contents
- [Installation](#installation)
- [Features](#features)
- [Quick Start](#quick-start)
- [Sync vs Async Usage](#sync-vs-async-usage)
  - [When to Use Each Version](#when-to-use-each-version)
  - [Basic Examples](#basic-examples)
  - [Advanced Async Features](#advanced-async-features)
  - [Migration and Compatibility](#migration-and-compatibility)
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

- **Dual API Support**: Both synchronous and asynchronous interfaces for all operations
- **Performance Optimized**: Connection pooling and session reuse for async operations
- **Safe by Default**: Automatic detection and prevention of event loop conflicts
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

## Quick Start

### Synchronous Usage (Simple)
```python
from xian_py import Xian, Wallet

# Create wallet and client
wallet = Wallet()
xian = Xian('http://node-ip:26657', wallet=wallet)

# Check balance
balance = xian.get_balance(wallet.public_key)
print(f"Balance: {balance}")

# Send transaction
result = xian.send(amount=10, to_address='recipient_address')
print(f"Transaction successful: {result['success']}")
```

### Asynchronous Usage (Performance)
```python
import asyncio
from xian_py import XianAsync, Wallet

async def main():
    wallet = Wallet()
    
    # Use context manager for automatic session cleanup
    async with XianAsync('http://node-ip:26657', wallet=wallet) as xian:
        # Check balance
        balance = await xian.get_balance(wallet.public_key)
        print(f"Balance: {balance}")
        
        # Send transaction
        result = await xian.send(amount=10, to_address='recipient_address')
        print(f"Transaction successful: {result['success']}")

asyncio.run(main())
```

## Sync vs Async Usage

The SDK provides both synchronous (`Xian`) and asynchronous (`XianAsync`) clients. Understanding when and how to use each is crucial for building efficient applications.

### When to Use Each Version

#### Use Synchronous (`Xian`) when:
- Building simple scripts or CLI tools
- Working in Jupyter notebooks or interactive environments
- Integrating with synchronous codebases
- Learning or prototyping
- Making occasional blockchain calls

#### Use Asynchronous (`XianAsync`) when:
- Building web applications or APIs
- Handling multiple concurrent blockchain operations
- Integrating with async frameworks (FastAPI, aiohttp, etc.)
- Building high-performance applications
- Making frequent blockchain calls

### Basic Examples

#### Synchronous Example
```python
from xian_py import Xian, Wallet

# Simple, straightforward usage
wallet = Wallet()
xian = Xian('http://node-ip:26657', wallet=wallet)

# All operations are blocking
balance = xian.get_balance(wallet.public_key)
tx_result = xian.send(100, 'recipient_address')
contract_state = xian.get_state('currency', 'balances', wallet.public_key)
```

#### Asynchronous Example
```python
import asyncio
from xian_py import XianAsync, Wallet

async def main():
    wallet = Wallet()
    
    # Context manager ensures proper cleanup
    async with XianAsync('http://node-ip:26657', wallet=wallet) as xian:
        # Concurrent operations for better performance
        balance, contract_state = await asyncio.gather(
            xian.get_balance(wallet.public_key),
            xian.get_state('currency', 'balances', wallet.public_key)
        )
        
        # Sequential operation
        tx_result = await xian.send(100, 'recipient_address')

asyncio.run(main())
```

### Advanced Async Features

#### Connection Pooling and Session Management

The async client uses connection pooling for optimal performance:

```python
from xian_py import XianAsync
import aiohttp

# Default configuration (recommended)
async with XianAsync('http://node-ip:26657') as xian:
    # Automatic session management with:
    # - Connection pooling (limit=100)
    # - DNS caching (TTL=300s)
    # - Timeouts (total=15s, connect=3s, read=10s)
    pass

# Custom configuration
custom_timeout = aiohttp.ClientTimeout(total=30, sock_connect=5)
custom_connector = aiohttp.TCPConnector(limit=200, ttl_dns_cache=600)

async with XianAsync(
    'http://node-ip:26657',
    timeout=custom_timeout,
    connector=custom_connector
) as xian:
    # Use custom settings
    pass

# Manual session management (advanced)
xian = XianAsync('http://node-ip:26657')
try:
    # Session created on first use
    result = await xian.get_balance('address')
finally:
    # Always close when not using context manager
    await xian.close()
```

#### Concurrent Operations

Maximize performance with concurrent requests:

```python
import asyncio
from xian_py import XianAsync, Wallet

async def check_multiple_balances(addresses):
    async with XianAsync('http://node-ip:26657') as xian:
        # Fetch all balances concurrently
        balances = await asyncio.gather(*[
            xian.get_balance(addr) for addr in addresses
        ])
        return dict(zip(addresses, balances))

async def deploy_multiple_contracts(contracts):
    async with XianAsync('http://node-ip:26657') as xian:
        # Deploy contracts concurrently
        results = await asyncio.gather(*[
            xian.submit_contract(name, code) 
            for name, code in contracts.items()
        ], return_exceptions=True)
        
        # Handle results and exceptions
        for (name, _), result in zip(contracts.items(), results):
            if isinstance(result, Exception):
                print(f"Failed to deploy {name}: {result}")
            else:
                print(f"Deployed {name}: {result['success']}")
```

### Migration and Compatibility

#### Using Async Code in Sync Contexts

Sometimes you need to call async code from synchronous code. The SDK provides the `run_sync` helper for this:

```python
from xian_py import XianAsync, run_sync

# In synchronous code (e.g., a CLI tool)
def get_balance_sync(address):
    async def _get_balance():
        async with XianAsync('http://node-ip:26657') as xian:
            return await xian.get_balance(address)
    
    # run_sync handles the event loop for you
    return run_sync(_get_balance())

# This works in any sync context
balance = get_balance_sync('some_address')
print(f"Balance: {balance}")
```

#### Advanced: Escaping Event Loop Conflicts

If you're already in an async context but need to run async code synchronously (rare but sometimes necessary):

```python
from xian_py import run_sync

async def some_async_function():
    # This would normally raise an error
    # result = run_sync(async_operation())
    
    # Use allow_thread=True to run in a separate thread
    result = run_sync(async_operation(), allow_thread=True)
    return result
```

⚠️ **Warning**: Using `allow_thread=True` runs the operation in a separate thread with a new event loop. Be aware of:
- Context variables won't be shared
- Thread safety considerations
- Potential performance overhead

#### Gradual Migration Strategy

Migrating from sync to async:

```python
# Step 1: Start with sync code
from xian_py import Xian

xian = Xian('http://node-ip:26657')
balance = xian.get_balance('address')

# Step 2: Prepare async version alongside
from xian_py import XianAsync
import asyncio

async def get_balance_async(address):
    async with XianAsync('http://node-ip:26657') as xian:
        return await xian.get_balance(address)

# Step 3: Use run_sync during transition
from xian_py import run_sync

def transitional_get_balance(address, use_async=False):
    if use_async:
        return run_sync(get_balance_async(address))
    else:
        xian = Xian('http://node-ip:26657')
        return xian.get_balance(address)

# Step 4: Eventually move to full async
```

### Error Handling

Both sync and async clients handle errors the same way:

```python
# Synchronous
from xian_py import Xian, XianException

try:
    xian = Xian('http://node-ip:26657')
    result = xian.send_tx('contract', 'function', {})
except XianException as e:
    print(f"Blockchain error: {e}")

# Asynchronous
from xian_py import XianAsync, XianException

async def safe_transaction():
    try:
        async with XianAsync('http://node-ip:26657') as xian:
            result = await xian.send_tx('contract', 'function', {})
    except XianException as e:
        print(f"Blockchain error: {e}")
```

### Best Practices

1. **Always use context managers with async client**:
   ```python
   # Good
   async with XianAsync(node_url) as xian:
       await xian.get_balance(address)
   
   # Avoid (unless you handle cleanup)
   xian = XianAsync(node_url)
   await xian.get_balance(address)
   # Don't forget: await xian.close()
   ```

2. **Batch operations when possible**:
   ```python
   # Good - concurrent execution
   results = await asyncio.gather(
       xian.get_balance(addr1),
       xian.get_balance(addr2),
       xian.get_state('contract', 'var', 'key')
   )
   
   # Less efficient - sequential execution
   balance1 = await xian.get_balance(addr1)
   balance2 = await xian.get_balance(addr2)
   state = await xian.get_state('contract', 'var', 'key')
   ```

3. **Choose the right client for your use case**:
   ```python
   # For scripts and simple tools
   from xian_py import Xian
   
   # For web apps and high-performance needs
   from xian_py import XianAsync
   ```

4. **Handle connection errors gracefully**:
   ```python
   async def resilient_balance_check(address, retries=3):
       for attempt in range(retries):
           try:
               async with XianAsync('http://node-ip:26657') as xian:
                   return await xian.get_balance(address)
           except Exception as e:
               if attempt == retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)  # Exponential backoff
   ```

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

**Synchronous:**
```python
from xian_py import Wallet, Xian

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

**Asynchronous:**
```python
import asyncio
from xian_py import Wallet, XianAsync

async def token_operations():
    wallet = Wallet()
    async with XianAsync('http://node-ip:26657', wallet=wallet) as xian:
        # Check balance
        balance = await xian.get_balance('address')
        
        # Send tokens with automatic stamp calculation
        result = await xian.send(amount=10, to_address='recipient_address')
        
        # Check custom token balance
        token_balance = await xian.get_balance('contract_address', contract='token_contract')
        
        return balance, result, token_balance

# Run the async function
asyncio.run(token_operations())
```

### Smart Contract Operations

#### Contract Deployment and Interaction

**Synchronous:**
```python
from xian_py import Wallet, Xian

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

**Asynchronous:**
```python
import asyncio
from xian_py import Wallet, XianAsync

async def contract_operations():
    wallet = Wallet()
    async with XianAsync('http://node-ip:26657', wallet=wallet) as xian:
        # Deploy contract
        code = '''
        @export
        def greet(name: str):
            return f"Hello, {name}!"
        '''
        result = await xian.submit_contract('greeting_contract', code)
        
        # Get contract state
        state = await xian.get_state('contract_name', 'variable_name', 'key')
        
        # Get and decompile contract source
        source = await xian.get_contract('contract_name', clean=True)
        
        return result, state, source

asyncio.run(contract_operations())
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

**Synchronous:**
```python
from xian_py import Wallet, Xian

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

**Asynchronous:**
```python
import asyncio
from xian_py import Wallet, XianAsync

async def send_transaction():
    wallet = Wallet()
    async with XianAsync('http://node-ip:26657', wallet=wallet) as xian:
        result = await xian.send_tx(
            contract='currency',
            function='transfer',
            kwargs={
                'to': 'recipient',
                'amount': 1000,
            }
        )
        return result

asyncio.run(send_transaction())
```

### Simulated Transactions

The SDK supports transaction simulation for two primary purposes:
1. Estimating stamp costs before broadcasting a transaction
2. Executing read-only contract functions without spending stamps

#### Low-Level Transaction with Transaction Cost Estimation

**Synchronous:**
```python
from xian_py import Wallet, Xian
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

**Asynchronous:**
```python
import asyncio
from xian_py import Wallet, XianAsync
from xian_py.transaction import get_nonce_async, create_tx, simulate_tx_async, broadcast_tx_sync_async

async def low_level_transaction():
    # Initialize wallet and client
    wallet = Wallet()
    node_url = 'http://node-ip:26657'
    
    async with XianAsync(node_url, wallet=wallet) as xian:
        # Get chain ID asynchronously
        chain_id = await xian.get_chain_id()
        
        # Prepare transaction payload
        payload = {
            "chain_id": chain_id,
            "contract": "currency",
            "function": "transfer",
            "kwargs": {"to": "recipient", "amount": 100},
            "nonce": await get_nonce_async(node_url, wallet.public_key),
            "sender": wallet.public_key,
            "stamps_supplied": 0
        }
        
        # Simulate to get stamp cost
        simulated = await simulate_tx_async(node_url, payload)
        print(f"Required stamps: {simulated['stamps_used']}")
        
        # Use the simulated stamps in the actual transaction
        payload['stamps_supplied'] = simulated['stamps_used']
        
        # Create and broadcast transaction
        tx = create_tx(payload, wallet)
        result = await broadcast_tx_sync_async(node_url, tx)
        
        return result

asyncio.run(low_level_transaction())
```

#### Read-Only Contract Execution

You can execute read-only contract functions without spending stamps by using transaction simulation. This is useful for querying contract state or calculating values without modifying the blockchain.

In the payload for a simulated transaction you don't need to specify the following keys:
- stamps_supplied
- chain_id
- nonce

**Synchronous:**
```python
from xian_py import Wallet, Xian
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

**Asynchronous:**
```python
import asyncio
from xian_py import Wallet, XianAsync
from xian_py.transaction import simulate_tx_async

async def read_only_execution():
    wallet = Wallet()
    node_url = 'http://node-ip:26657'
    
    # Prepare read-only query payload
    payload = {
        "contract": "token_contract",
        "function": "get_balance",
        "kwargs": {"address": wallet.public_key},
        "sender": wallet.public_key,
    }
    
    # Execute simulation and get result
    result = await simulate_tx_async(node_url, payload)
    print(f"Balance: {result['result']}")
    return result['result']

# Or use the high-level interface
async def read_only_with_client():
    wallet = Wallet()
    async with XianAsync('http://node-ip:26657', wallet=wallet) as xian:
        # The simulate method handles the payload construction
        result = await xian.simulate(
            contract="token_contract",
            function="get_balance",
            kwargs={"address": wallet.public_key}
        )
        return result['result']

asyncio.run(read_only_execution())
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

## Real-World Examples

### Building a Token Transfer Service

Here's a complete example of a service that handles token transfers with proper error handling and retry logic:

**Synchronous Version:**
```python
from xian_py import Xian, Wallet, XianException
import time

class TokenTransferService:
    def __init__(self, node_url: str, wallet: Wallet):
        self.xian = Xian(node_url, wallet=wallet)
        self.wallet = wallet
    
    def transfer_with_retry(self, to_address: str, amount: float, 
                          token: str = "currency", max_retries: int = 3):
        """Transfer tokens with automatic retry on failure"""
        for attempt in range(max_retries):
            try:
                # Check balance first
                balance = self.xian.get_balance(self.wallet.public_key, contract=token)
                if balance < amount:
                    raise ValueError(f"Insufficient balance: {balance} < {amount}")
                
                # Send the transaction
                result = self.xian.send_tx(
                    contract=token,
                    function="transfer",
                    kwargs={"to": to_address, "amount": amount}
                )
                
                if result['success']:
                    return result
                else:
                    raise XianException(f"Transaction failed: {result['message']}")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None

# Usage
wallet = Wallet('your_private_key')
service = TokenTransferService('http://node-ip:26657', wallet)

try:
    result = service.transfer_with_retry('recipient_address', 100.0)
    print(f"Transfer successful! TX Hash: {result['tx_hash']}")
except Exception as e:
    print(f"Transfer failed: {e}")
```

**Asynchronous Version (High Performance):**
```python
import asyncio
from xian_py import XianAsync, Wallet, XianException
from typing import List, Dict, Optional

class AsyncTokenTransferService:
    def __init__(self, node_url: str, wallet: Wallet):
        self.node_url = node_url
        self.wallet = wallet
        self.xian: Optional[XianAsync] = None
    
    async def __aenter__(self):
        self.xian = await XianAsync(self.node_url, wallet=self.wallet).__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.xian:
            await self.xian.__aexit__(exc_type, exc_val, exc_tb)
    
    async def transfer_with_retry(self, to_address: str, amount: float,
                                token: str = "currency", max_retries: int = 3):
        """Transfer tokens with automatic retry on failure"""
        for attempt in range(max_retries):
            try:
                # Check balance first
                balance = await self.xian.get_balance(self.wallet.public_key, contract=token)
                if balance < amount:
                    raise ValueError(f"Insufficient balance: {balance} < {amount}")
                
                # Send the transaction
                result = await self.xian.send_tx(
                    contract=token,
                    function="transfer",
                    kwargs={"to": to_address, "amount": amount}
                )
                
                if result['success']:
                    return result
                else:
                    raise XianException(f"Transaction failed: {result['message']}")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def batch_transfer(self, transfers: List[Dict[str, any]]):
        """Execute multiple transfers concurrently"""
        tasks = []
        for transfer in transfers:
            task = self.transfer_with_retry(
                transfer['to'],
                transfer['amount'],
                transfer.get('token', 'currency')
            )
            tasks.append(task)
        
        # Execute all transfers concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = []
        failed = []
        for transfer, result in zip(transfers, results):
            if isinstance(result, Exception):
                failed.append({'transfer': transfer, 'error': str(result)})
            else:
                successful.append({'transfer': transfer, 'result': result})
        
        return {'successful': successful, 'failed': failed}

# Usage
async def main():
    wallet = Wallet('your_private_key')
    
    async with AsyncTokenTransferService('http://node-ip:26657', wallet) as service:
        # Single transfer
        result = await service.transfer_with_retry('recipient_address', 100.0)
        print(f"Transfer successful! TX Hash: {result['tx_hash']}")
        
        # Batch transfers
        transfers = [
            {'to': 'address1', 'amount': 50.0},
            {'to': 'address2', 'amount': 75.0},
            {'to': 'address3', 'amount': 100.0, 'token': 'custom_token'}
        ]
        
        batch_results = await service.batch_transfer(transfers)
        print(f"Successful: {len(batch_results['successful'])}")
        print(f"Failed: {len(batch_results['failed'])}")

asyncio.run(main())
```

### DeFi Application Example

Building a simple DeFi swap interface:

```python
import asyncio
from xian_py import XianAsync, Wallet, run_sync
from typing import Optional

class DeFiSwapInterface:
    def __init__(self, node_url: str, wallet: Wallet, dex_contract: str):
        self.node_url = node_url
        self.wallet = wallet
        self.dex_contract = dex_contract
    
    async def get_price(self, token_in: str, token_out: str, amount_in: float) -> float:
        """Get swap price without executing the swap"""
        async with XianAsync(self.node_url, wallet=self.wallet) as xian:
            result = await xian.simulate(
                contract=self.dex_contract,
                function="get_amount_out",
                kwargs={
                    "token_in": token_in,
                    "token_out": token_out,
                    "amount_in": amount_in
                }
            )
            return result['result']
    
    async def execute_swap(self, token_in: str, token_out: str, 
                          amount_in: float, min_amount_out: float) -> dict:
        """Execute a token swap"""
        async with XianAsync(self.node_url, wallet=self.wallet) as xian:
            # First approve the DEX to spend tokens
            approve_result = await xian.send_tx(
                contract=token_in,
                function="approve",
                kwargs={
                    "to": self.dex_contract,
                    "amount": amount_in
                }
            )
            
            if not approve_result['success']:
                raise Exception(f"Approval failed: {approve_result['message']}")
            
            # Execute the swap
            swap_result = await xian.send_tx(
                contract=self.dex_contract,
                function="swap",
                kwargs={
                    "token_in": token_in,
                    "token_out": token_out,
                    "amount_in": amount_in,
                    "min_amount_out": min_amount_out
                }
            )
            
            return swap_result
    
    # Synchronous wrapper for use in non-async code
    def get_price_sync(self, token_in: str, token_out: str, amount_in: float) -> float:
        """Synchronous version of get_price"""
        return run_sync(self.get_price(token_in, token_out, amount_in))

# Async usage
async def async_defi_example():
    wallet = Wallet()
    defi = DeFiSwapInterface('http://node-ip:26657', wallet, 'dex_contract')
    
    # Get swap price
    price = await defi.get_price('token_a', 'token_b', 100.0)
    print(f"Swap price: {price}")
    
    # Execute swap with 2% slippage
    min_output = price * 0.98
    result = await defi.execute_swap('token_a', 'token_b', 100.0, min_output)
    print(f"Swap executed: {result}")

# Sync usage (e.g., in a CLI tool)
def sync_defi_example():
    wallet = Wallet()
    defi = DeFiSwapInterface('http://node-ip:26657', wallet, 'dex_contract')
    
    # Use the sync wrapper
    price = defi.get_price_sync('token_a', 'token_b', 100.0)
    print(f"Swap price: {price}")

# Run examples
asyncio.run(async_defi_example())
# or
sync_defi_example()
```

### WebSocket Integration for Real-time Updates

```python
import asyncio
import aiohttp
from xian_py import XianAsync, Wallet
import json

class XianRealtimeClient:
    def __init__(self, node_url: str, ws_url: str, wallet: Wallet):
        self.node_url = node_url
        self.ws_url = ws_url
        self.wallet = wallet
    
    async def monitor_transactions(self, address: str):
        """Monitor real-time transactions for an address"""
        async with XianAsync(self.node_url, wallet=self.wallet) as xian:
            # Get initial balance
            balance = await xian.get_balance(address)
            print(f"Initial balance: {balance}")
            
            # Connect to WebSocket for real-time updates
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.ws_url) as ws:
                    # Subscribe to address events
                    await ws.send_json({
                        "jsonrpc": "2.0",
                        "method": "subscribe",
                        "params": {
                            "query": f"tm.event='Tx' AND transfer.to='{address}'"
                        },
                        "id": 1
                    })
                    
                    # Process incoming transactions
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if 'result' in data:
                                # New transaction detected
                                tx_hash = data['result']['events']['tx.hash'][0]
                                
                                # Get transaction details
                                tx_details = await xian.get_tx(tx_hash)
                                print(f"New transaction: {tx_details}")
                                
                                # Update balance
                                new_balance = await xian.get_balance(address)
                                print(f"Updated balance: {new_balance}")

# Usage
async def main():
    wallet = Wallet()
    client = XianRealtimeClient(
        'http://node-ip:26657',
        'ws://node-ip:26657/websocket',
        wallet
    )
    
    # Monitor transactions for your wallet
    await client.monitor_transactions(wallet.public_key)

asyncio.run(main())
```