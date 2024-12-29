import json
import base64
import decimal

from xian_py.xian_datetime import Datetime, Timedelta
from xian_py.xian_decimal import ContractingDecimal, fix_precision

MIN_INT = -(2 ** 63)
MAX_INT = 2 ** 63 - 1


class Encoder(json.JSONEncoder):
    def default(self, o, *args):
        if isinstance(o, Datetime) or o.__class__.__name__ == Datetime.__name__:
            return {
                '__time__': [o.year, o.month, o.day, o.hour, o.minute, o.second, o.microsecond]
            }
        elif isinstance(o, Timedelta) or o.__class__.__name__ == Timedelta.__name__:
            return {
                '__delta__': [o._timedelta.days, o._timedelta.seconds]
            }
        elif isinstance(o, bytes):
            return {
                '__bytes__': o.hex()
            }
        elif isinstance(o, decimal.Decimal) or o.__class__.__name__ == decimal.Decimal.__name__:
            # return format(o, f'.{MAX_LOWER_PRECISION}f')
            return {
                '__fixed__': str(fix_precision(o))
            }

        elif isinstance(o, ContractingDecimal) or o.__class__.__name__ == ContractingDecimal.__name__:
            # return format(o._d, f'.{MAX_LOWER_PRECISION}f')
            return {
                '__fixed__': str(fix_precision(o._d))
            }
        # else:
        #    return safe_repr(o)
        return super().default(o)


# TODO: This was initially done for MongoDB. Maybe we can now adjust that
# JSON library from Python 3 doesn't let you instantiate your custom Encoder. You have to pass it as an obj to json
def encode(data: [str, int, dict]):
    """ NOTE:
    Normally encoding behavior is overriden in 'default' method inside
    a class derived from json.JSONEncoder. Unfortunately this can be done only
    for custom types.

    Due to MongoDB integer limitation (8 bytes), we need to preprocess 'big' integers.
    """
    if isinstance(data, int):
        data = encode_int(data)
    elif isinstance(data, dict):
        data = encode_ints_in_dict(data)

    return json.dumps(data, cls=Encoder, separators=(',', ':'))


def encode_int(value: int):
    if MIN_INT < value < MAX_INT:
        return value

    return {
        '__big_int__': str(value)
    }


def encode_kv(key, value):
    # if key is None:
    #     key = ''
    #
    # if value is None:
    #     value = ''

    k = key.encode()
    v = encode(value).encode()
    return k, v


def encode_ints_in_dict(data: dict):
    d = dict()
    for k, v in data.items():
        if isinstance(v, int):
            d[k] = encode_int(v)
        elif isinstance(v, dict):
            d[k] = encode_ints_in_dict(v)
        elif isinstance(v, list):
            d[k] = []
            for i in v:
                if isinstance(i, dict):
                    d[k].append(encode_ints_in_dict(i))
                elif isinstance(i, int):
                    d[k].append(encode_int(i))
                else:
                    d[k].append(i)
        else:
            d[k] = v

    return d


def as_object(d):
    if '__time__' in d:
        return Datetime(*d['__time__'])
    elif '__delta__' in d:
        return Timedelta(days=d['__delta__'][0], seconds=d['__delta__'][1])
    elif '__bytes__' in d:
        return bytes.fromhex(d['__bytes__'])
    elif '__fixed__' in d:
        return ContractingDecimal(d['__fixed__'])
    elif '__big_int__' in d:
        return int(d['__big_int__'])
    return dict(d)


# Decode has a hook for JSON objects, which are just Python dictionaries. You have to specify the logic in this hook.
# This is not uniform, but this is how Python made it.
def decode(data):
    if data is None:
        return None

    if isinstance(data, bytes):
        data = data.decode()

    try:
        return json.loads(data, object_hook=as_object)
    except json.decoder.JSONDecodeError as e:
        return None

def decode_dict(encoded_dict: str) -> dict:
    decoded_data = decode_str(encoded_dict)
    decoded_tx = bytes.fromhex(decoded_data).decode('utf-8')
    return json.loads(decoded_tx)


def decode_str(encoded_data: str) -> str:
    decoded_bytes = base64.b64decode(encoded_data)
    return decoded_bytes.decode('utf-8')


def decode_kv(key, value):
    k = key.decode()
    v = decode(value)
    # if v == '':
    #     v = None
    return k, v


TYPES = {'__fixed__', '__delta__', '__bytes__', '__time__', '__big_int__'}


def convert(k, v):
    if k == '__fixed__':
        return ContractingDecimal(v)
    elif k == '__delta__':
        return Timedelta(days=v[0], seconds=v[1])
    elif k == '__bytes__':
        return bytes.fromhex(v)
    elif k == '__time__':
        return Datetime(*v)
    elif k == '__big_int__':
        return int(v)
    return v


def convert_dict(d):
    if not isinstance(d, dict):
        return d

    d2 = dict()
    for k, v in d.items():
        if k in TYPES:
            return convert(k, v)

        elif isinstance(v, dict):
            d2[k] = convert_dict(v)

        elif isinstance(v, list):
            d2[k] = []
            for i in v:
                d2[k].append(convert_dict(i))

        else:
            d2[k] = v

    return d2
