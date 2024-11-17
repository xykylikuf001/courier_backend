try:
    from .cryptography_backend import get_random_bytes  # noqa: F401
except ImportError:
    from .native import get_random_bytes  # noqa: F401

try:
    from .cryptography_backend import CryptographyRSAKey as RSAKey  # noqa: F401
except ImportError:
    try:
        from .rsa_backend import RSAKey  # noqa: F401
    except ImportError:
        RSAKey = None

try:
    from .cryptography_backend import CryptographyECKey as ECKey  # noqa: F401
except ImportError:
    from .ecdsa_backend import ECDSAECKey as ECKey  # noqa: F401

try:
    from .cryptography_backend import CryptographyAESKey as AESKey  # noqa: F401
except ImportError:
    AESKey = None

try:
    from .cryptography_backend import CryptographyHMACKey as HMACKey  # noqa: F401
except ImportError:
    from .native import HMACKey  # noqa: F401

from .base import DIRKey  # noqa: F401
