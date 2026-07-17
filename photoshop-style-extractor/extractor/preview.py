from PIL import Image


def save_preview(psd, out_path: str, max_side: int = 1200) -> str | None:
    try:
        image = psd.composite()
        if image is None:
            return None
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGB")
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.getchannel("A"))
            image = background
        longest = max(image.size)
        if longest > max_side:
            scale = max_side / longest
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.LANCZOS)
        image.save(out_path, "JPEG", quality=85)
        return out_path
    except Exception:
        return None
