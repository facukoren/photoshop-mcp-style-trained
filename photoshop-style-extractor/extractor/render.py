from extractor.model import GlobalStyle, BrandStyle


def _fmt_counts(items, unit="veces"):
    return "\n".join(f"- `{item}` — {count} {unit}" for item, count in items) or "- (nada detectado)"


def _fmt_canvases(items):
    lines = []
    for (w, h), count in items:
        lines.append(f"- {w}×{h} px — {count} piezas")
    return "\n".join(lines) or "- (nada detectado)"


def render_style_guide(glob: GlobalStyle) -> str:
    return f"""# Guía de estilo — ADN de diseño global

> Generado automáticamente a partir de {glob.psd_count} PSDs.
> Marcas detectadas: {", ".join(glob.brands) or "(ninguna)"}.

## ✍️ Corregí esto
Este archivo es un punto de partida. Editá lo que no te represente:
si una fuente o color aparece por casualidad, borralo; si falta tu
criterio (ej. "los titulares siempre van arriba"), agregalo en prosa.

## Tipografías más usadas
{_fmt_counts(glob.fonts, "capas de texto")}

## Paleta global
{_fmt_counts(glob.colors, "capas")}

## Tamaños de lienzo
{_fmt_canvases(glob.canvas_sizes)}

## Efectos de capa frecuentes
{_fmt_counts(glob.effects, "capas")}
"""


def render_brand(brand: BrandStyle) -> str:
    return f"""# Kit de marca — {brand.brand}

> {brand.piece_count} piezas analizadas.

## Paleta
{_fmt_counts(brand.colors, "capas")}

## Tipografías
{_fmt_counts(brand.fonts, "capas de texto")}

## Tamaños de lienzo
{_fmt_canvases(brand.canvas_sizes)}

## Efectos frecuentes
{_fmt_counts(brand.effects, "capas")}

## Nombres de capa típicos
{_fmt_counts(brand.layer_names, "piezas")}

## Composición (posición vertical de los textos)
{_fmt_counts(brand.text_bands, "capas de texto")}
"""


def render_recipe(brand: BrandStyle) -> str:
    top_canvas = brand.canvas_sizes[0][0] if brand.canvas_sizes else (1080, 1080)
    layers = "\n".join(f"   - {name}" for name, _ in brand.layer_names[:8]) or "   - (sin datos)"
    return f"""# Receta — pieza típica de {brand.brand}

> Punto de partida editable, derivado de las piezas analizadas.

**Lienzo sugerido:** {top_canvas[0]}×{top_canvas[1]} px

**Estructura típica de capas (de abajo hacia arriba):**
{layers}

**Pasos sugeridos:**
1. Crear el lienzo en el tamaño sugerido.
2. Colocar el fondo / imagen base.
3. Aplicar el tratamiento de color de la marca.
4. Montar los textos con la tipografía y paleta de la marca.
5. Agregar logo y CTA.
6. Revisar contra las referencias visuales de la marca.
"""


def render_report(fonts: list[str], unreadable: list[tuple[str, str]], psd_count: int) -> str:
    font_lines = "\n".join(f"- [ ] {f}" for f in fonts) or "- (ninguna detectada)"
    if unreadable:
        bad_lines = "\n".join(f"- `{path}` — {err}" for path, err in unreadable)
    else:
        bad_lines = "- (todos los PSDs se leyeron correctamente)"
    return f"""# Reporte de extracción

PSDs analizados con éxito: **{psd_count}**

## Fuentes a verificar instaladas en la PC con Photoshop
Marcá cada una cuando confirmes que está instalada:

{font_lines}

## PSDs no legibles (salteados)
{bad_lines}
"""
