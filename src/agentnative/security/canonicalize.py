from __future__ import annotations

from urllib.parse import unquote


class SecretCanonicalizer:
    """Produce a small, deterministic set of URL-decoded detection variants."""

    def __init__(self, max_decode_passes: int = 2) -> None:
        if max_decode_passes < 0 or max_decode_passes > 3:
            raise ValueError("max_decode_passes must be between 0 and 3")
        self.max_decode_passes = max_decode_passes

    def variants(self, value: str) -> tuple[str, ...]:
        current = str(value)
        variants = [current]
        for _ in range(self.max_decode_passes):
            decoded = unquote(current)
            if decoded == current:
                break
            variants.append(decoded)
            current = decoded
        return tuple(variants)


def canonicalize_for_secret_detection(value: str) -> tuple[str, ...]:
    return SecretCanonicalizer().variants(value)

