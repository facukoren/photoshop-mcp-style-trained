from collections import Counter
from extractor.model import PSDRecord, BrandStyle, GlobalStyle

_BAND_ORDER = {"arriba": 0, "centro": 1, "abajo": 2}


def _ranked_list(counter: Counter):
    return sorted(counter.items(), key=lambda kv: (-kv[1], str(kv[0])))


def _band_of(bbox: tuple[int, int, int, int], canvas_height: int) -> str:
    if canvas_height <= 0:
        return "centro"
    center_y = (bbox[1] + bbox[3]) / 2
    if center_y < canvas_height / 3:
        return "arriba"
    if center_y < canvas_height * 2 / 3:
        return "centro"
    return "abajo"


def _text_bands(records: list[PSDRecord]) -> list[tuple[str, int]]:
    bands: Counter = Counter()
    for rec in records:
        if rec.error is not None:
            continue
        for layer in rec.layers:
            if layer.text is not None:
                bands[_band_of(layer.bbox, rec.height)] += 1
    # orden lógico arriba→abajo, no por frecuencia
    return sorted(bands.items(), key=lambda kv: _BAND_ORDER.get(kv[0], 9))


def _collect(records: list[PSDRecord]):
    fonts, colors, canvases, effects, names = (
        Counter(), Counter(), Counter(), Counter(), Counter())
    for rec in records:
        if rec.error is not None:
            continue
        canvases[(rec.width, rec.height)] += 1
        for layer in rec.layers:
            if layer.kind == "error":
                continue
            names[layer.name] += 1
            for effect in layer.effects:
                effects[effect] += 1
            for color in layer.colors:
                colors[color] += 1
            if layer.text is not None:
                for font in layer.text.fonts:
                    fonts[font] += 1
    return fonts, colors, canvases, effects, names


def aggregate(records: list[PSDRecord]) -> tuple[GlobalStyle, list[BrandStyle]]:
    readable = [r for r in records if r.error is None]
    brands_seen: list[str] = []
    for rec in readable:
        if rec.brand not in brands_seen:
            brands_seen.append(rec.brand)

    brand_styles: list[BrandStyle] = []
    for brand in brands_seen:
        subset = [r for r in readable if r.brand == brand]
        fonts, colors, canvases, effects, names = _collect(subset)
        brand_styles.append(BrandStyle(
            brand=brand, piece_count=len(subset),
            fonts=_ranked_list(fonts), colors=_ranked_list(colors),
            canvas_sizes=_ranked_list(canvases), effects=_ranked_list(effects),
            layer_names=_ranked_list(names), text_bands=_text_bands(subset),
        ))

    g_fonts, g_colors, g_canvases, g_effects, _g_names = _collect(readable)
    glob = GlobalStyle(
        brands=brands_seen, psd_count=len(readable),
        fonts=_ranked_list(g_fonts), colors=_ranked_list(g_colors),
        canvas_sizes=_ranked_list(g_canvases), effects=_ranked_list(g_effects),
    )
    return glob, brand_styles


def list_fonts(records: list[PSDRecord]) -> list[str]:
    seen = set()
    for rec in records:
        if rec.error is not None:
            continue
        for layer in rec.layers:
            if layer.text is not None:
                seen.update(layer.text.fonts)
    return sorted(seen)


def list_unreadable(records: list[PSDRecord]) -> list[tuple[str, str]]:
    return [(r.path, r.error) for r in records if r.error is not None]
