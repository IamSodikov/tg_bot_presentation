# utils/formatting.py
def format_amount_short(n: int | None, *, use_cyrillic: bool = False) -> str:
    """25000 -> 25K, 1_000_000 -> 1KK, 1_500_000 -> 1.5KK, va h.k."""
    if n is None:
        return "—"
    k = "К" if use_cyrillic else "K"

    if n >= 1_000_000:
        if n % 1_000_000 == 0:
            return f"{n // 1_000_000}{k}{k}"
        v = n / 1_000_000
        s = f"{v:.1f}".rstrip("0").rstrip(".")
        return f"{s}{k}{k}"

    if n >= 1_000:
        if n % 1_000 == 0:
            return f"{n // 1_000}{k}"
        v = n / 1_000
        s = f"{v:.1f}".rstrip("0").rstrip(".")
        return f"{s}{k}"

    return str(n)
