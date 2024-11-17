import base64
import struct
from datetime import timedelta
from typing import Union, Callable, Optional

# Piggyback of the backends implementation of the function that converts a long
# to a bytes stream. Some plumbing is necessary to have the signatures match.
try:
    from cryptography.utils import int_to_bytes as _long_to_bytes


    def long_to_bytes(n: int, block_size: Optional[int] = 0) -> bytes:
        return _long_to_bytes(n, block_size or None)


except ImportError:
    from ecdsa.ecdsa import int_to_string as _long_to_bytes


    def long_to_bytes(n: int, block_size: Optional[int] = 0) -> bytes:
        ret = _long_to_bytes(n)
        if block_size == 0:
            return ret
        else:
            assert len(ret) <= block_size
            padding = block_size - len(ret)
            return b"\x00" * padding + ret


def long_to_base64(data: int, size: Optional[int] = 0) -> bytes:
    return base64.urlsafe_b64encode(long_to_bytes(data, size)).strip(b"=")


def int_arr_to_long(arr) -> int:
    return int("".join(["%02x" % byte for byte in arr]), 16)


def base64_to_long(data: Union[str, bytes]) -> int:
    if isinstance(data, str):
        data = data.encode("ascii")

    # urlsafe_b64decode will happily convert b64encoded data
    _d = base64.urlsafe_b64decode(bytes(data) + b"==")
    return int_arr_to_long(struct.unpack("%sB" % len(_d), _d))


def calculate_at_hash(access_token: str, hash_alg: Callable) -> str:
    """Helper method for calculating an access token
    hash, as described in http://openid.net/specs/openid-connect-core-1_0.html#CodeIDToken

    Its value is the base64url encoding of the left-most half of the hash of the octets
    of the ASCII representation of the access_token value, where the hash algorithm
    used is the hash algorithm used in the alg Header Parameter of the ID Token's JOSE
    Header. For instance, if the alg is RS256, hash the access_token value with SHA-256,
    then take the left-most 128 bits and base64url encode them. The at_hash value is a
    case-sensitive string.

    Args:
        access_token (str): An access token string.
        hash_alg (callable): A callable returning a hash object, e.g. hashlib.sha256

    """
    hash_digest = hash_alg(access_token.encode("utf-8")).digest()
    cut_at = int(len(hash_digest) / 2)
    truncated = hash_digest[:cut_at]
    at_hash = base64url_encode(truncated)
    return at_hash.decode("utf-8")


def base64url_decode(input_str: bytes) -> bytes:
    """Helper method to base64url_decode a string.

    Args:
        input_str (bytes): A base64url_encoded string to decode.

    """
    rem = len(input_str) % 4

    if rem > 0:
        input_str += b"=" * (4 - rem)

    return base64.urlsafe_b64decode(input_str)


def base64url_encode(input_str: bytes) -> bytes:
    """Helper method to base64url_encode a string.

    Args:
        input_str (bytes): A base64url_encoded string to encode.

    """
    return base64.urlsafe_b64encode(input_str).replace(b"=", b"")


def timedelta_total_seconds(delta: timedelta) -> int:
    """Helper method to determine the total number of seconds
    from a timedelta.

    Args:
        delta (timedelta): A timedelta to convert to seconds.
    """
    return delta.days * 24 * 60 * 60 + delta.seconds


def ensure_binary(s: Union[str, bytes]) -> bytes:
    """Coerce **s** to bytes."""

    if isinstance(s, bytes):
        return s
    if isinstance(s, str):
        return s.encode("utf-8", "strict")
    raise TypeError(f"not expecting type '{type(s)}'")
