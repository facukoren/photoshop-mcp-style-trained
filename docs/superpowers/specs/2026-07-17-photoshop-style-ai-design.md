# Diseño: AI que diseña en Photoshop con el estilo de Facu

**Fecha:** 2026-07-17
**Autor:** Facu + Claude (sesión de brainstorming)
**Estado:** Aprobado — pendiente de plan de implementación

---

## 1. Objetivo

Construir un sistema donde, a partir de un brief en lenguaje natural (español),
una AI diseñe piezas de social media/marketing en Adobe Photoshop **con el estilo
de diseño de Facu**, usando la mayor cantidad posible de herramientas de Photoshop,
y entregando archivos PSD editables por capas.

Dos modos de uso, ambos requeridos:

1. **Brief → diseño completo**: "Hacé un post para [marca] sobre [tema]" → PSD terminado en su estilo.
2. **Copiloto en vivo**: Facu trabaja en Photoshop y pide acciones puntuales ("aplicale mi tratamiento de color", "armame la base tipográfica").

**Requisito duro de usabilidad:** el uso diario tiene que ser tan simple como chatear,
para que colegas no técnicos puedan usarlo sin tocar código ni terminal.

## 2. Contexto y decisiones clave

- **No se hace fine-tuning del modelo.** El "estilo" se captura como una capa de
  conocimiento en archivos de texto + referencias visuales que Claude consulta en cada
  diseño. Esto lo hace inspeccionable, corregible y versionable — se entrena con el uso,
  no con reentrenamientos.
- **No se construye el control de Photoshop desde cero.** Se reutiliza un MCP comunitario
  existente y probado. El esfuerzo de desarrollo va íntegro a lo que no existe: la capa de estilo.
- **El desarrollo del extractor y la capa de estilo se hacen en la PC actual**
  (no requiere Photoshop). La ejecución corre en la PC que tiene Photoshop instalado.

### Enfoque elegido: A — MCP existente + capa de estilo propia

Descartados:
- **B (MCP desde cero):** semanas reconstruyendo lo que ya existe (puente UXP/COM, ~80 tools,
  manejo de errores) antes de tocar la parte de estilo. Reservado como plan B parcial: si al
  MCP elegido le falta una herramienta, se forkea y se agrega solo esa.
- **C (Cloud oficial de Adobe):** opera sobre archivos vía API cloud; no cumple el modo
  copiloto en vivo y cubre un subconjunto chico de herramientas. Se evalúa solo como
  complemento futuro (Firefly para generación de imágenes).

### MCP candidato

`alisaitteke/photoshop-mcp` (~80 herramientas, sistema de recetas para workflows multi-paso,
UI web propia). Alternativas de respaldo a validar en implementación:
`loonghao/photoshop-python-api-mcp-server` (COM de Windows), `dcc-mcp-photoshop` (UXP WebSocket),
`airtaxi/PhotoshopMcpServer` (COM). La elección final se confirma probando cobertura de
herramientas y estabilidad en la PC con Photoshop.

## 3. Arquitectura

Tres componentes, repartidos entre dos PCs.

```
PC DE DESARROLLO (actual — sin Photoshop)
┌───────────────────────────────────────────────┐
│ 1. EXTRACTOR DE ESTILO (Python + psd-tools)   │
│    Lee 20+ PSDs → produce ADN de diseño       │
│                    │                          │
│                    ▼                          │
│ 2. CAPA DE ESTILO (carpeta portable)          │
│    style-guide.md · brands/*.md ·             │
│    recipes/*.md · references/*.jpg            │
└───────────────────────────────────────────────┘
                     │ (se copia)
                     ▼
PC CON PHOTOSHOP (uso diario)
┌───────────────────────────────────────────────┐
│ 3. EJECUCIÓN                                  │
│    Claude Desktop + MCP Photoshop +           │
│    skill "diseñar como Facu"                  │
└───────────────────────────────────────────────┘
```

### 3.1 Extractor de estilo

- **Qué hace:** recorre los PSDs y extrae a texto estructurado:
  - Tipografías: familias, pesos, escalas de tamaño, tracking/leading recurrentes.
  - Paletas de color: globales y por marca.
  - Efectos de capa: sombras, trazos, degradados, modos de fusión.
  - Estructura: jerarquía de capas/grupos, convenciones de nombres.
  - Lienzos: tamaños/relaciones de aspecto usados.
  - Composición: posiciones recurrentes de titulares, logos, CTAs.
  - Preview JPG de cada PSD para la biblioteca de referencias.
- **Entrada:** carpeta con los .psd (copiados a esta PC).
- **Salida:** los archivos de la capa de estilo (sección 3.2) + un reporte de fuentes usadas
  y de PSDs no legibles.
- **Corregible:** la salida es texto legible; Facu revisa y edita lo que no lo represente.
- **Dependencia:** `psd-tools` (Python). No requiere Photoshop.

### 3.2 Capa de estilo (carpeta portable)

- `style-guide.md` — ADN de diseño global de Facu.
- `brands/<cliente>.md` — kit por marca: colores, logos, tipografías, tono.
- `recipes/<tipo>.md` — recetas paso a paso de tipos de pieza frecuentes (ej. post de promo,
  flyer de evento), derivadas de cómo están construidos los PSDs.
- `references/<pieza>.jpg` — previews de las mejores piezas, para inspección visual de la AI.
- **Portabilidad:** es una carpeta; se copia a la PC con Photoshop y Claude la carga como skill.

### 3.3 Ejecución

- **Cliente:** Claude Desktop (chat) en la PC con Photoshop. Los colegas nunca ven terminal.
- **Skill "diseñar como Facu":** al recibir un pedido, carga automáticamente el style guide,
  el kit de la marca pedida y la receta del tipo de pieza.
- **Flujo brief → diseño:**
  1. Interpretar el pedido (marca, tipo de pieza, tema, assets provistos).
  2. Elegir receta y kit de marca.
  3. Construir el diseño capa por capa vía MCP.
  4. Exportar preview.
  5. Auto-crítica: comparar la preview contra las referencias de estilo.
  6. Corregir e iterar.
  7. Entregar PSD editable + preview.
- **Flujo copiloto:** mismo sistema operando sobre el documento ya abierto por Facu.

## 4. Assets e imágenes

- **Fotos del cliente:** se arrastran al chat; el sistema las recorta/retoca/compone.
- **Biblioteca propia:** el sistema busca en la carpeta de recursos propios de Facu.
- **Generación con IA (fase 1):** el Generative Fill de Photoshop no se automatiza de forma
  confiable; cuando haga falta un fondo/elemento generado, la AI lo solicita y Facu lo genera
  con un click. Integración de Firefly API = extensión futura opcional.

## 5. Manejo de errores

- **Nunca se trabaja sobre originales:** siempre sobre copias, con versiones incrementales
  guardadas durante el diseño.
- **PSDs no legibles por el extractor:** se saltean y se reportan al final; no frenan el proceso.
- **Falla de una herramienta de Photoshop en vivo:** reintento por camino alternativo; si no
  es posible, se reporta exactamente qué quedó pendiente (sin inventar resultados).
- **Herramienta faltante en el MCP:** se forkea el MCP y se agrega (plan B previsto).

## 6. Criterio de éxito

1. **Test del extractor:** Facu lee el style guide generado y confirma "así diseño yo"
   (corrigiendo lo que no).
2. **Test de recreación:** dado solo el brief de 3 piezas ya hechas, comparar el resultado
   contra los originales.
3. **Test de colegas:** un colega, sin ayuda, pide una pieza real y la puede usar.

## 7. Usabilidad para colegas

- **Uso diario:** abrir Claude Desktop, escribir el pedido en español, arrastrar fotos. Nada más.
- **Complejidad acotada a la instalación inicial** (una vez por PC): instalar MCP, conectarlo a
  Claude, copiar la carpeta de estilo. Se resuelve con un instalador automatizado + guía con
  capturas (meta: ~10 min por PC nueva).
- **Requisito por colega:** cuenta de Claude (plan pago para uso intensivo).

## 8. Limitaciones conocidas

- No es un clon perfecto desde el día 1; meta 70–90% de fidelidad, creciente con uso/correcciones.
- Generative Fill no automatizable de forma confiable en fase 1.
- Las fuentes deben estar instaladas en la PC con Photoshop (el extractor entrega la lista exacta).
- El MCP es comunitario; posible fork si falta cobertura o hay inestabilidad.

## 9. Fases de implementación

1. **Fase 1 — Extractor + capa de estilo** (PC actual): construir el extractor, correrlo sobre
   los PSDs, generar y validar la capa de estilo con Facu.
2. **Fase 2 — Ejecución** (PC con Photoshop): instalar y validar el MCP, construir la skill
   "diseñar como Facu", probar los flujos brief→diseño y copiloto.
3. **Fase 3 — Instalador para colegas**: automatizar setup + guía.
4. **Fase 4 — Extensiones**: Firefly API, producción en lote.

## 10. Fuera de alcance (por ahora)

- Fine-tuning de modelos.
- Bancos de stock (Freepik/Shutterstock/etc.).
- Automatización de Generative Fill.
- Producción en lote (Fase 4).
