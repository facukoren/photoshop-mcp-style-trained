import os
from psd_tools import PSDImage
from extractor.model import LayerRecord, TextInfo, PSDRecord
from extractor.colors import dominant_colors
from extractor.preview import save_preview


def _effect_names(layer) -> list[str]:
    if not getattr(layer, "has_effects", False):
        return []
    names: list[str] = []
    try:
        for effect in layer.effects:
            names.append(type(effect).__name__.lower())
    except Exception:
        pass
    return names


def _text_info(layer) -> TextInfo | None:
    if getattr(layer, "kind", None) != "type":
        return None
    try:
        text_value = layer.text or ""
    except Exception:
        text_value = ""
    fonts = list(getattr(layer, "font_names", []) or [])
    return TextInfo(text=text_value, fonts=fonts, sizes_px=[], colors=[])


def layer_to_record(layer, depth: int) -> LayerRecord:
    try:
        colors = dominant_colors(layer.composite())
    except Exception:
        colors = []
    text = _text_info(layer)
    if text is not None:
        text.colors = colors
    return LayerRecord(
        name=getattr(layer, "name", "?"),
        kind=getattr(layer, "kind", "unknown"),
        visible=bool(getattr(layer, "visible", True)),
        opacity=int(getattr(layer, "opacity", 255)),
        blend_mode=getattr(getattr(layer, "blend_mode", None), "name", "normal"),
        bbox=tuple(getattr(layer, "bbox", (0, 0, 0, 0))),
        depth=depth,
        effects=_effect_names(layer),
        colors=colors,
        text=text,
    )


def walk_layers(layers, depth: int = 0) -> list[LayerRecord]:
    records: list[LayerRecord] = []
    for layer in layers:
        try:
            record = layer_to_record(layer, depth)
        except Exception:
            records.append(LayerRecord(
                name=getattr(layer, "name", "?"), kind="error", visible=False,
                opacity=0, blend_mode="normal", bbox=(0, 0, 0, 0), depth=depth,
                effects=[], colors=[], text=None,
            ))
            continue
        records.append(record)
        if getattr(layer, "is_group", False):
            records.extend(walk_layers(layer, depth + 1))
    return records


def read_psd(path: str, brand: str, preview_dir: str | None = None) -> PSDRecord:
    try:
        psd = PSDImage.open(path)
    except Exception as exc:
        return PSDRecord(
            path=path, brand=brand, width=0, height=0, color_mode="?",
            layers=[], preview_path=None, error=f"{type(exc).__name__}: {exc}",
        )
    record = PSDRecord(
        path=path, brand=brand,
        width=int(psd.width), height=int(psd.height),
        color_mode=getattr(psd.color_mode, "name", str(psd.color_mode)),
        layers=walk_layers(psd), preview_path=None, error=None,
    )
    if preview_dir is not None:
        os.makedirs(preview_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(path))[0]
        out = os.path.join(preview_dir, f"{base}.jpg")
        record.preview_path = save_preview(psd, out)
    return record
