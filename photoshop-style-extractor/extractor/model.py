from dataclasses import dataclass, field


@dataclass
class TextInfo:
    text: str
    fonts: list[str] = field(default_factory=list)
    sizes_px: list[float] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)


@dataclass
class LayerRecord:
    name: str
    kind: str
    visible: bool
    opacity: int
    blend_mode: str
    bbox: tuple[int, int, int, int]
    depth: int
    effects: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    text: TextInfo | None = None


@dataclass
class PSDRecord:
    path: str
    brand: str
    width: int
    height: int
    color_mode: str
    layers: list[LayerRecord] = field(default_factory=list)
    preview_path: str | None = None
    error: str | None = None


@dataclass
class BrandStyle:
    brand: str
    piece_count: int
    fonts: list[tuple[str, int]] = field(default_factory=list)
    colors: list[tuple[str, int]] = field(default_factory=list)
    canvas_sizes: list[tuple[tuple[int, int], int]] = field(default_factory=list)
    effects: list[tuple[str, int]] = field(default_factory=list)
    layer_names: list[tuple[str, int]] = field(default_factory=list)
    text_bands: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class GlobalStyle:
    brands: list[str]
    psd_count: int
    fonts: list[tuple[str, int]] = field(default_factory=list)
    colors: list[tuple[str, int]] = field(default_factory=list)
    canvas_sizes: list[tuple[tuple[int, int], int]] = field(default_factory=list)
    effects: list[tuple[str, int]] = field(default_factory=list)
