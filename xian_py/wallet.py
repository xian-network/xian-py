import secrets

from bip_utils.utils.mnemonic import Mnemonic
from nacl.signing import SigningKey, VerifyKey
from nacl.public import SealedBox, PublicKey
from nacl.exceptions import BadSignatureError
from nacl.bindings import crypto_sign_ed25519_pk_to_curve25519

from bip_utils import (
    Bip39MnemonicGenerator,
    Bip39SeedGenerator,
    Bip39WordsNum,
    Bip32Slip10Ed25519
)

def encrypt_msg(receiver_public_key: str, cleartext_msg: str) -> str:
    """ Encrypts message. Requires receiver's public key """
    # Convert Ed25519 public key to X25519 public key
    ed25519_pk_bytes = bytes.fromhex(receiver_public_key)
    x25519_pk_bytes = crypto_sign_ed25519_pk_to_curve25519(ed25519_pk_bytes)
    x25519_pk = PublicKey(x25519_pk_bytes)

    sealed_box = SealedBox(x25519_pk)
    encrypted = sealed_box.encrypt(cleartext_msg.encode('utf-8'))
    return encrypted.hex()

def decrypt_msg(receiver_private_key: str, encrypted_msg: str) -> str:
    """ Decrypt message. Requires receiver's private key """
    # Convert Ed25519 private key (seed) to X25519 private key
    ed25519_seed = bytes.fromhex(receiver_private_key)
    sk = SigningKey(ed25519_seed)
    x25519_sk = sk.to_curve25519_private_key()

    sealed_box = SealedBox(x25519_sk)
    plaintext = sealed_box.decrypt(bytes.fromhex(encrypted_msg))
    return plaintext.decode('utf-8')

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

def key_is_valid(key: str):
    """ Check if the given address is valid.
     Can be used with public and private keys """
    if not len(key) == 64:
        return False
    try:
        int(key, 16)
    except:
        return False
    return True

class Wallet:
    def __init__(self, seed: str=None):
        if seed:
            seed = bytes.fromhex(seed)
        else:
            seed = secrets.token_bytes(32)

        self.sk = SigningKey(seed=seed)
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

class HDWallet:
    def __init__(self, mnemonic: str=None):
        if mnemonic:
            self.mnemonic = Mnemonic(mnemonic.split())
        else:
            self.mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)

        self.seed_bytes = Bip39SeedGenerator(self.mnemonic).Generate()
        self.master_key = Bip32Slip10Ed25519.FromSeed(self.seed_bytes)

    @property
    def mnemonic_str(self) -> str:
        """ Returns the mnemonic seed as a string """
        return str(self.mnemonic)

    @property
    def mnemonic_lst(self) -> list[str]:
        """ Returns the mnemonic seed as a list of strings """
        return str(self.mnemonic).split()

    def get_wallet(self, derivation_path):
        child_key = self.master_key
        for index in derivation_path:
            # Automatically harden the index
            hardened_index = index + 0x80000000
            child_key = child_key.ChildKey(hardened_index)
        private_key_hex = child_key.PrivateKey().Raw().ToHex()
        return Wallet(seed=private_key_hex)
