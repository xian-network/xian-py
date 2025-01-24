import secrets

from bip_utils.utils.mnemonic import Mnemonic
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError

from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip39WordsNum,
    Bip32Slip10Ed25519,
    Bip32Secp256k1,
    Bip44,
    Bip44Coins,
    Bip44Changes
)

try:
    from eth_account import Account
    from eth_account.messages import encode_defunct
    from eth_utils import to_checksum_address

    ETHEREUM_SUPPORT = True
except ImportError:
    ETHEREUM_SUPPORT = False


def verify_msg(public_key: str, msg: str, signature: str) -> bool:
    """ Verify signed message by public key """
    signature = bytes.fromhex(signature)
    pk = bytes.fromhex(public_key)
    msg = msg.encode()

    try:
        VerifyKey(pk).verify(msg, signature)
    except BadSignatureError:
        return False
    return True


class Wallet:
    def __init__(self, private_key: str = None):
        if private_key:
            private_key = bytes.fromhex(private_key)
        else:
            private_key = secrets.token_bytes(32)

        self.sk = SigningKey(seed=private_key)
        self.vk = self.sk.verify_key

    @property
    def private_key(self):
        return self.sk.encode().hex()

    @property
    def public_key(self):
        return self.vk.encode().hex()

    def sign_msg(self, msg: str):
        """ Sign message with private key """
        sig = self.sk.sign(msg.encode())
        return sig.signature.hex()

    def verify_msg(self, msg: str, signature: str) -> bool:
        """ Verify signed message """
        signature = bytes.fromhex(signature)
        msg = msg.encode()
        try:
            self.vk.verify(msg, signature)
        except BadSignatureError:
            return False
        return True

    @staticmethod
    def is_valid_key(key: str) -> bool:
        """ Check if the given key (public or private) is valid """
        if not len(key) == 64:
            return False
        try:
            int(key, 16)
        except:
            return False
        return True


class EthereumWallet:
    def __init__(self, private_key: str = None):
        if private_key:
            private_key = bytes.fromhex(private_key)
        else:
            private_key = secrets.token_bytes(32)

        self.account = Account.from_key(private_key)

    @property
    def private_key(self):
        return self.account.key.hex()

    @property
    def public_key(self):
        return self.account.address

    def sign_msg(self, msg: str):
        """ Sign message with private key """
        message = encode_defunct(text=msg)
        signed_message = self.account.sign_message(message)
        return signed_message.signature.hex()

    def verify_msg(self, msg: str, signature: str) -> bool:
        """ Verify signed message """
        message = encode_defunct(text=msg)
        try:
            recovered_address = Account.recover_message(message, signature=bytes.fromhex(signature))
            return recovered_address.lower() == self.public_key.lower()
        except:
            return False

    @staticmethod
    def is_valid_key(key: str) -> bool:
        """ Check if the given key is a valid Ethereum address """
        try:
            # Ethereum addresses are 40 hex chars (not counting '0x')
            if key.startswith('0x'):
                key = key[2:]
            if len(key) != 40:
                return False
            int(key, 16)
            return True
        except:
            return False


class HDWallet:
    def __init__(self, mnemonic: str = None):
        if mnemonic:
            self.mnemonic = Mnemonic(mnemonic.split())
        else:
            self.mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)

        self.seed_bytes = Bip39SeedGenerator(self.mnemonic).Generate()

        # Initialize ED25519 master key
        self.ed25519_master_key = Bip32Slip10Ed25519.FromSeed(self.seed_bytes)

        # Only initialize secp256k1 if ethereum support is installed
        if ETHEREUM_SUPPORT:
            self.secp256k1_master_key = Bip32Secp256k1.FromSeed(self.seed_bytes)

    @property
    def mnemonic_str(self) -> str:
        """ Returns the mnemonic seed as a string """
        return str(self.mnemonic)

    @property
    def mnemonic_lst(self) -> list[str]:
        """ Returns the mnemonic seed as a list of strings """
        return str(self.mnemonic).split()

    def get_wallet(self, derivation_path):
        """Get ED25519 wallet for custom derivation path"""
        child_key = self.ed25519_master_key
        for index in derivation_path:
            # Automatically harden the index
            hardened_index = index + 0x80000000
            child_key = child_key.ChildKey(hardened_index)
        private_key_hex = child_key.PrivateKey().Raw().ToHex()
        return Wallet(private_key=private_key_hex)

    def get_ethereum_wallet(self, account_idx: int = 0):
        """Get Ethereum wallet for specific account index"""
        if not ETHEREUM_SUPPORT:
            raise ImportError("Ethereum support not installed. Install with 'pip install xian-py[eth]'")

        bip44_ctx = Bip44.FromSeed(self.seed_bytes, Bip44Coins.ETHEREUM)
        account_keys = bip44_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
        eth_child_key = account_keys.AddressIndex(account_idx)
        private_key_hex = eth_child_key.PrivateKey().Raw().ToHex()
        return EthereumWallet(private_key=private_key_hex)
