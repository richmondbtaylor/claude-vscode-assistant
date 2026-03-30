# JSON Schema Reference

## Element Types

| Type | Use For |
|---|---|
| `rectangle` | Processes, actions, components |
| `ellipse` | Entry/exit points, external systems, marker dots |
| `diamond` | Decisions, conditionals |
| `arrow` | Connections between shapes |
| `text` | Labels, free-floating text |
| `line` | Non-arrow structural connections |
| `frame` | Grouping containers |

## Common Properties (all elements)

| Property | Type | Description |
|---|---|---|
| `id` | string | Unique identifier (use descriptive names like `"trigger_rect"`) |
| `type` | string | Element type |
| `x`, `y` | number | Position in pixels |
| `width`, `height` | number | Size in pixels |
| `strokeColor` | string | Border color (hex) |
| `backgroundColor` | string | Fill color (hex or `"transparent"`) |
| `fillStyle` | string | `"solid"`, `"hachure"`, `"cross-hatch"` |
| `strokeWidth` | number | 1 (thin), 2 (standard), 3 (bold) |
| `strokeStyle` | string | `"solid"`, `"dashed"`, `"dotted"` |
| `roughness` | number | 0 (smooth), 1 (default), 2 (rough) |
| `opacity` | number | Always 100 |
| `seed` | number | Random seed for roughness |
| `angle` | number | Rotation in radians (usually 0) |
| `version` | number | 1 |
| `versionNonce` | number | Any unique number |
| `isDeleted` | boolean | false |
| `groupIds` | array | [] |
| `boundElements` | array/null | References to bound text elements |
| `link` | null | null |
| `locked` | boolean | false |

## Text-Specific Properties

| Property | Description |
|---|---|
| `text` | Display text (readable words ONLY) |
| `originalText` | Same as `text` |
| `fontSize` | 16–20px recommended |
| `fontFamily` | Always `3` (monospace) |
| `textAlign` | `"left"`, `"center"`, `"right"` |
| `verticalAlign` | `"top"`, `"middle"`, `"bottom"` |
| `containerId` | ID of parent shape (null for free-floating) |
| `lineHeight` | 1.25 |

## Arrow-Specific Properties

| Property | Description |
|---|---|
| `points` | Array of `[x, y]` coordinates (relative to arrow's x,y) |
| `startBinding` | Connection to start shape |
| `endBinding` | Connection to end shape |
| `startArrowhead` | `null`, `"arrow"`, `"bar"`, `"dot"`, `"triangle"` |
| `endArrowhead` | `null`, `"arrow"`, `"bar"`, `"dot"`, `"triangle"` |

## Binding Format

```json
{ "elementId": "shapeId", "focus": 0, "gap": 2 }
```

When a shape has a bound arrow, its `boundElements` array must reference the arrow:
```json
"boundElements": [{"id": "arrow1", "type": "arrow"}]
```

When a shape has bound text, its `boundElements` must reference the text:
```json
"boundElements": [{"id": "text1", "type": "text"}]
```

## Rectangle Roundness

```json
"roundness": { "type": 3 }
```

## Seed Namespacing (for large diagrams)

Namespace seeds by section to avoid collisions:
- Section 1: 100001, 100002, 100003...
- Section 2: 200001, 200002, 200003...
- Section 3: 300001, 300002, 300003...
