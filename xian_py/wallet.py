import secrets

from nacl.signing import SigningKey, VerifyKey
from nacl.public import SealedBox, PublicKey, PrivateKey
from nacl.exceptions import BadSignatureError


def encrypt_msg(receiver_public_key: str, cleartext_msg: str):
    """ Encrypts message. Requires receiver's public key """
    sealed_box = SealedBox(PublicKey(bytes.fromhex(receiver_public_key)))
    encrypted = sealed_box.encrypt(cleartext_msg.encode('utf-8'))
    return encrypted.hex()


def decrypt_msg(receiver_private_key: str, encrypted_msg: str):
    """ Decrypt message. Requires receiver's private key """
    sealed_box = SealedBox(PrivateKey(bytes.fromhex(receiver_private_key)))
    plaintext = sealed_box.decrypt(bytes.fromhex(encrypted_msg))
    return plaintext.decode('utf-8')


def verify_msg(public_key: str, msg: str, signature: str) -> bool:
    """  """
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
    def __init__(self, seed=None):
        if isinstance(seed, str):
            seed = bytes.fromhex(seed)

        if seed is None:
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
