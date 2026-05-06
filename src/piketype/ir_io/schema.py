"""IR schema versioning.

Every IR file on disk carries the integer ``SCHEMA_VERSION``. Bump on
any breaking change to IR shape: renamed/removed fields, changed value
encoding, changed discriminator names. Additive-only changes (new
optional fields with defaults) do NOT require a bump.

A version mismatch on read is fatal — surface it loudly and let the
user re-run ``piketype build``. Silent migration is intentionally not
supported.
"""

from __future__ import annotations

from piketype.errors import PikeTypeError


SCHEMA_VERSION: int = 1


class IRSchemaMismatchError(PikeTypeError):
    """Raised when an IR file's schema_version does not match this build."""
