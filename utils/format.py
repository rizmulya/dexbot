def fnum(number):
    """
    Mengubah angka menjadi format yang lebih manusiawi dengan suffix k, M, B, dll.
    
    Contoh:
    - 1000 → 1k
    - 1_500_000 → 1.5M
    - 2_000_000_000 → 2B
    """
    if not isinstance(number, (int, float)):
        return number 
    
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"  # Miliar
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"  # Juta
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"  # Ribu
    else:
        return str(number)