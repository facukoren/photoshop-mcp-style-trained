import os


def discover_psds(root: str) -> list[tuple[str, str]]:
    root = os.path.abspath(root)
    found: list[tuple[str, str]] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if not name.lower().endswith(".psd"):
                continue
            full = os.path.join(dirpath, name)
            parent = os.path.abspath(dirpath)
            if parent == root:
                brand = "sin-marca"
            else:
                brand = os.path.basename(parent)
            found.append((full, brand))
    found.sort(key=lambda pair: pair[0].lower())
    return found
