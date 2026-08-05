[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | 🌐 **Español**

# sovereign-skills v6.5.8

20 habilidades para el ciclo de vida completo de proyectos con Claude Code — desde la configuración hasta el flujo de trabajo diario, revisión de código, gestión de sesiones y gobernanza. Cada habilidad funciona de forma independiente; la secuencia completa cubre todas las etapas.

> **Cambios en v6.5.8:** Versión de refinamiento — no se añadieron ni eliminaron habilidades; se hizo un port selectivo de los cambios del fork interno desde v6.5.7 (6 de las 20 habilidades cambiaron upstream en ese período, más un port de `code-autopsy` diffeado a mano). `doc-drift` (nueva señal de Derivabilidad — una línea que codifica de forma fija un hecho reconstruible mecánicamente desde el código se marca como estructuralmente propensa a drift incluso si el valor actual es correcto), `integration-intake` (nueva verificación de trampa de analogía — una afirmación de valor del tipo "X lo hace así, así que nosotros también" necesita responder tres preguntas antes de contar como evidencia), `session-start` (nueva regla de carga condicionada a la consulta para archivos de memoria bajo demanda — cargar solo después de confirmar que la conversación realmente trata ese tema, no por mera coincidencia de palabras clave), `goal-lock` (nuevo campo opcional EVAL TYPE para tareas que miden la fiabilidad de una habilidad/hook/puerta en sí misma, un antipatrón de Auto-corrección Silenciosa, un Registro de Primer Intento que guarda la ejecución cruda de DONE EVIDENCE antes de cualquier cambio, una nota de Límite de Autoduda Temprana contra el abandono prematuro de tareas por mal cálculo del presupuesto restante), `pre-push` (cuando code-reviewer no está disponible, ahora recurre a una revisión abreviada en línea en vez de omitirse por completo; nuevo Paso 3.5 Public-Mirror Scrub — un respaldo de solo advertencia en el momento del push para repos que son espejos públicos curados de una fuente privada; nueva segunda pasada opcional de barrido de brechas de alto riesgo y nuevo reataque paralelo multiángulo opcional; registro de motivo de omisión añadido al bucle de corrección), `session-checkpoint` (nueva Etapa 1, encolado de promoción a CT — `scripts/ct_promotion_queue.py`, opcional mediante un archivo marcador, agrupamiento puramente determinista por solapamiento de tokens sin juicio de LLM y sin escribir en MEMORY.md/context-log.md, incluye una suite de regresión con 35 casos; la condición de omisión del registro de invocaciones se aclaró para reutilizar solo las ramas de volumen de actividad de la Triple Gate, excluyendo deliberadamente la rama de 24h pensada para un disparador automático distinto), `code-autopsy` (7 términos más de code smells + nombrado explícito del principio SOLID violado en cambios de dirección de dependencia, una verificación de corrección de reenvío en wrapper/proxy, una verificación de violación de reglas rectoras solo por cita textual sin inferir "intención", Q3 ganó off-by-one/falsy-zero/restos de copiar-pegar/regex sin escapar más las trampas de Python de argumento por defecto mutable y closures de enlace tardío, la verificación de fuga de memoria de Q7 ahora nombra el patrón de objeto grande capturado por closure, STEP 0 ganó una verificación de contrato a nivel de función + fijación explícita del alcance del diff + descubrimiento de CLAUDE.md/rules rectores, una nueva verificación de invariante restablecido para cada línea eliminada/reemplazada, y un nuevo nivel [FAST MODE] (`--fast`) entre el pipeline completo y el Modo Rápido).

> **Cambios en v6.5.7:** Versión de refinamiento — no se añadieron ni eliminaron habilidades; varias obtuvieron scripts deterministas funcionales en lugar de autopuntuación por LLM. `project-overview` (`generate_overview.py` ya no es un stub — ahora implementa por completo el parseo del registro, la extracción de state-snapshot y el render/replace del bloque AUTO, con escapado de celdas de tabla para entrada no confiable y recuperación de marcadores malformados, respaldado por pruebas unitarias + de integración), `scope` (la puerta de ambigüedad Quick/Full y la validación de mínimo de ítems de BRIEF.md ahora pasan por un `ambiguity_gate.py` portado, con una prueba de regresión que fija un bug de conteo de texto en negrita como encabezado), `skill-ops` → v1.2 (la clasificación por buckets del Modo Health y la puntuación S/U/S_Q del Modo Quality ahora pasan por `skill_health_bucket.py` en lugar de aritmética manual), `collab-audit` (el filtrado de higiene de origen del Paso 0.6 ahora pasa por `session_hygiene_scan.py`), `session-checkpoint` (nuevo paso de Discoverability Check que marca escrituras de memoria sin backlink de índice, una protección contra salida parcial por timeout/kill, dos puertas de calidad de lecciones Reflexion, una regla de redacción de PII para observaciones crudas, y la verificación de Key Files trasladada a un script `validate_memory_claims.py`), `goal-lock` (la superficie de scope-check ampliada a cambios de interfaz/API y no solo archivos tocados, una nota de variable dominante de longitud de cadena respaldada por benchmark, la puerta de orden del Stop-hook actualizada a una implementación verificada de 4 condiciones, una nueva sección de Safety Layers, etiquetas de fallo VERIFY estilo enum, una advertencia de autojuicio en el DELTA CHECK de REFINE, y un protocolo de terminación para tareas en segundo plano), `code-autopsy` (una Rationalization Table con 8 racionalizaciones comunes de revisores + sus refutaciones, y una nota que recomienda aritmética de severidad basada en script en vez de cálculo mental), `eval-leakage-audit` (taxonomía de 17→18 patrones — añade coevolución de Goodhart en bucles de automejora — más una verificación honesta de 4 etiquetas de Independencia del Revisor), `integration-intake` (frontmatter `tools:` de solo lectura, entradas `not_for` de estilo redirección, 7 etiquetas fijas de enum de juicio erróneo por fase), `pre-push` (frontmatter explícito `depends_on`/`concurrency_profile`, una nota de Límite de Autonomía que distingue los comandos git de solo lectura del `git push` con puerta de control, un enlace de referencia a un catálogo de seguridad externo), `session-start` (frontmatter `depends_on`/`concurrency_profile`, las Fases 2.2-2.4 reescritas como comandos deterministas con contratos de stdout fijos, una nueva sección de Herencia L0 sin numerar), `doc-drift` (nuevo Paso 0 de prefiltro determinista que alimenta la categoría Riesgoso/Ambiguo solo como evidencia de apoyo), y frontmatter `depends_on`/`concurrency_profile` adoptado en `full-audit`, `project-check`, `project-init`, `freeze`, `stepback`, `next-action` y `clean-room`, varios de los cuales también obtuvieron tablas de Scope Boundary etiquetadas por categoría de herramienta. **Brecha conocida expuesta por esta versión**: `project-check` (y algunos afines) obtuvieron notas sin numerar de "principio heredado" en los encabezados de Safety Layers/Error Recovery — una versión pasada eliminó deliberadamente las citas numeradas `(L0 §N)` de esos mismos encabezados en las 10 habilidades; las notas de esta versión son sin numerar/genéricas en vez de las citas eliminadas, pero el patrón de anotación de encabezado en sí ha vuelto. Vale la pena una decisión consciente antes de que la próxima versión siga construyendo sobre esto.
>
> **Cambios en v6.5.6:** Versión de refinamiento — no se añadieron ni eliminaron habilidades. `eval-leakage-audit` (taxonomía de 13→17 patrones — enmascaramiento por respawn, pseudorreplicación, brecha de calibración de estímulo, omisiones de ahorro de costos sin auditar), `goal-lock` (una regla de parada S7 que bloquea forzar una implementación cuando la evidencia de ejecución contradice una instrucción explícita, una escalera de 5 niveles de rigor de evidencia + orden de reporte que prioriza los fallos + frases de cobertura prohibidas, un patrón de enmascaramiento de éxito por "layer laundering", y una nota de pre-especificación de rigor de evidencia), `full-audit` (una puerta de acumulación compuesta que marca el riesgo de muerte por mil cortes cuando se acumulan hallazgos UNCERTAIN/NIT en un área aunque cada uno se haya descartado individualmente, y un Assumption Ledger para veredictos CONFIRMED que dependen de supuestos no verificados), `session-checkpoint` (campos opcionales de lección `regime`/`escalate_if`, un campo opcional `outcomes` que rastrea first-attempt-pass/rework/resolvedBy, y una segunda condición OR de archivado de lecciones más una verificación cruzada obligatoria antes de archivar), `code-autopsy` → v7.2 (un vocabulario de code-smell para Q1, un requisito de escenario de fallo concreto, autorización a nivel de objeto bajo Q5, verificaciones ampliadas de red/DB/streaming/cache bajo Q7, una verificación de módulo superficial + conflicto de ADR bajo Q8, un sistema numérico de umbral de confianza, y un cambio de métrica de techo de resultado a métrica de proceso para comparaciones empatadas), `pre-push` → v3.8.0 (incorpora `scan_secrets.py` junto al `scan_secrets.pl` existente — se prefiere Python cuando está presente, Perl como respaldo — más `LICENSE.txt` para atribución upstream; nota: se descubrió que la cobertura de patrones de los dos escáneres difiere en esta versión, p. ej. el port de Python añade una verificación f13 de webhook de Slack ausente en Perl, y varios patrones existentes cubren un conjunto más estrecho o más amplio de variantes en cada lado — documentado como una brecha conocida, aún no reconciliada).
>
> **Cambios en v6.5.5:** Versión de refinamiento — no se añadieron ni eliminaron habilidades. `eval-leakage-audit` (taxonomía de 8→13 patrones — dual-fail-flag, autofalsificación de línea base asimétrica, evidence-burn, una verificación de 4 puertas para el calificador no calificado, detección de tareas con techo — más una lista de verificación de sustanciación de estratificación y un veredicto honesto de 4 etiquetas de independencia del revisor), `goal-lock` (una puerta de orden que bloquea la finalización cuando no se ejecutó ninguna verificación después de la última edición, ramificación de canal de evidencia para entregables sin código de salida, una verificación de comprensión, y tres nuevas protecciones contra enmascaramiento de éxito), `pre-push` → v3.7 (pase conjunto entre bundles + una puerta de falso positivo de tres estados), `integration-intake` (preclasificación de margen, terminación trait-vs-procedure, verificación triple de afirmaciones de efectividad), `session-start` (se añadió `claude-sonnet-5` a la lista blanca de IDs de modelo — corrigiendo una falsa advertencia de "modelo inválido"), `setup` (se eliminó un disparador `/setup` duplicado), `full-audit` (una capa de verificación de rule-dry-run), `clean-room` (reconciliado con el autobahn upstream v0.14.0 — un límite N=1 en el re-barrido independiente), `code-autopsy` (detección de redefinición de oráculo Q10), más refinamientos menores en `session-checkpoint`, `skill-ops`, `collab-audit` y `scope`.
>
> **Cambios en v6.5:** Nuevo: `eval-leakage-audit` (audita si un eval/métrica/holdout realmente asegura una verdad de referencia externa independiente o es una autoconfirmación circular, mediante una taxonomía de 8 patrones — solo lectura), `doc-drift` (audita la memoria/documentación que Claude Code carga en el contexto — CLAUDE.md/MEMORY.md/skills/agents/commands — buscando tres tipos de problemas: afirmaciones desactualizadas, contradicciones mutuas y redacción riesgosa/ambigua, produciendo una lista de correcciones priorizada). Actualizado: `project-init` (corregido un error de mayúsculas/minúsculas en el nombre de archivo — `skill.md`→`SKILL.md` — que podía hacer fallar la carga de skills en sistemas de archivos sensibles a mayúsculas, y externalizadas las plantillas de la Fase 3 a `references/templates.md`), `pre-push` → v3.6 (dos nuevos patrones del escáner de secretos — f11 cadenas de prompt-injection en diffs, f12 URLs de índices de cadena de suministro no-PyPI — más una verificación de salud del pipeline de hooks en el Paso 0), `scope` (añadida la regla de descubrimiento 10x para Mid-Task Scope Drift), `collab-audit` (añadido el Paso 0.6 Filtro de Higiene de Origen, que excluye sesiones de subagentes/hilos auto-derivadas para que no se confundan con sesiones orgánicas del usuario), `full-audit`/`integration-intake` (ambos ganaron una sección de Safety Layers; `integration-intake` también añadió un paso de Fase 1.8 de selección de superficie M-axis — determinar en qué superficie (prompt/regla/hook/skill) debería vivir un patrón antes de enrutarlo), `goal-lock` (añadida una plantilla de tarea `migration`), `project-overview` (añadida una Rationalization Table), `stepback` (añadida una sección de Dominant Variable + campos de frontmatter).
>
> **Cambios en v6.4:** Nuevo: `full-audit` (auditoría exhaustiva de un área completa — barrido determinista + revisión de contenido, mapa de cobertura persistente, kill-test anti-falsos-positivos), `integration-intake` (puerta de selección de 5 puntos para adoptar patrones externos de skills/agentes/reglas/plugins, con verificación de procedencia/inyección), `clean-room` (recorta solicitudes con elementos de seguridad hacia un alcance seguro, ejecutado por un subagente de contexto completamente aislado — adaptado de la skill "autobahn" de LilMGenius/paperthin bajo licencia MIT, con mejoras de aislamiento a nivel de sistema de archivos y de sincronización del registro). Actualizado: `goal-lock` (repite verbatim las CONSTRAINTS/SCOPE-Exclude en cada checkpoint de tareas largas), `session-checkpoint` (nueva fase de Attestation — registro de recibos evidence-chain con `handoff_attestation.py` incluido, para que el hook SessionStart de la siguiente sesión detecte manipulación del handoff).
>
> **Cambios en v6.3:** Nuevo: `skill-ops` (hub de snapshot/rollback + salud de uso + seguimiento de invocaciones), `next-action` (lee handoff/git/lessons/STATE y propone las 3 acciones principales según impacto), `project-overview` (mapa determinista del estado entre proyectos). `code-autopsy` → v7.1 (subverificaciones más profundas por pregunta), `pre-push` → v3.5 (9 patrones IOC de cadena de suministro), `goal-lock`/`session-checkpoint`/`session-start`/`scope`/`stepback`/`freeze` reforzados. Las 12 habilidades anteriores ganaron frontmatter `not_for` y `see_also` para mejor capacidad de descubrimiento.

---

## Inicio rápido

**Proyecto nuevo (15 min):**
```
/project-init       →  CLAUDE.md + ROADMAP + .gitignore + .env.example
/setup              →  rules/ + hooks + memory/ + enrutamiento de agentes + equipo
Diariamente:
  /session-start      al inicio de cada sesión
  /scope              antes de cada funcionalidad (definir IN/OUT/criterios de salida)
  /freeze             antes de implementar (declarar zona editable)
  /goal-lock          bloquear objetivo, forzar ciclo PLAN→DO→VERIFY
  /stepback           en cualquier momento — verificar dirección, 10 líneas
  /next-action        en cualquier momento — lee el estado actual y propone las 3 acciones principales
  /code-autopsy       revisión de código 12Q + puntuación + veredicto
  /pre-push           antes de cada push (escaneo de secretos + revisión AI)
  /session-checkpoint al final de cada sesión
```

**Proyecto existente (5 min):**
```
/project-check      →  Puntuación en 4 dimensiones + lista de brechas por severidad
/code-autopsy       →  Revisión de código 12Q (funciona como prompt independiente en cualquier LLM)
/collab-audit       →  Diagnóstico de colaboración AI en 14 secciones
```

**Gobernanza (según necesidad):**
```
/integration-intake →  antes de adoptar una habilidad/agente/regla/plugin externo — filtro de 5 puntos
/full-audit         →  auditoría exhaustiva de un área completa (código/docs/habilidades/memoria/config) con mapa de cobertura
/clean-room         →  cuando una tarea mezcla material relacionado con seguridad y trabajo genuinamente seguro
/eval-leakage-audit →  antes de confiar en un eval/métrica/holdout — comprobar autoconfirmación circular
/doc-drift          →  auditar el contexto cargado (CLAUDE.md/MEMORY.md/skills) por redacción desactualizada/contradictoria
```

---

## Habilidades

### Fase de configuración

| Habilidad | Función |
|-----------|---------|
| [project-init](../project-init/) | Scaffolding basado en entrevista — genera CLAUDE.md, ROADMAP, .gitignore, .env.example a partir de decisiones, no plantillas |
| [setup](../setup/) | Infraestructura Claude Code + equipo de agentes — rules, hooks, memory, enrutamiento e instalación de agentes en un solo flujo |

### Flujo de trabajo diario

| Habilidad | Función |
|-----------|---------|
| [scope](../scope/) | Definir IN/OUT/criterios de salida antes de implementar. Modo Quick (3 preguntas) o modo Full (especificación por capas) |
| [freeze](../freeze/) | Declarar la zona editable — todo lo demás queda congelado. Previene la expansión del alcance durante la implementación |
| [goal-lock](../goal-lock/) | Motor de disciplina de agentes — bloquea el objetivo, fuerza el ciclo PLAN→DO→VERIFY→FINALIZE→OUTPUT, detecta 13 patrones de enmascaramiento de éxito |
| [pre-push](../pre-push/) | Pipeline pre-push obligatorio — escaneo de secretos (12 patrones), build/test, lint, revisión de código AI en paralelo. Bloquea push ante hallazgos Critical/High |

### Revisión de código

| Habilidad | Función |
|-----------|---------|
| [code-autopsy](../code-autopsy/) | **Actualizado v7.2.** Revisión de código cuantificada 12Q — puntuación de 4 ejes (Security/Stability/Robustness/Operability), anclajes de severidad, veredicto de despliegue (SHIP/FIX/RISKY/BLOCK), gate de factualidad, detección de gaming CapCode, detección de errores fabricados CEF. Funciona como prompt independiente en cualquier LLM |

### Cambio de perspectiva

| Habilidad | Función |
|-----------|---------|
| [stepback](../stepback/) | **Actualizado.** Reinicio de perspectiva en un paso — 1 pregunta de reencuadre abstracto + 3 verificaciones rápidas (desvío de alcance, efectos secundarios, mejor enfoque) en menos de 10 líneas. Usar en cualquier momento durante el trabajo |
| [next-action](../next-action/) | **Nuevo.** Lee handoff/git/lessons/STATE y propone las 3 acciones principales según impacto. Solo propone, nunca ejecuta. Usar en cualquier momento |

### Gestión de sesiones

| Habilidad | Función |
|-----------|---------|
| [session-start](../session-start/) | Carga el handoff de la sesión anterior, revisa lecciones aprendidas, health check, señal de "listo" con acción prioritaria |
| [session-checkpoint](../session-checkpoint/) | Guarda el contexto de sesión antes del compact — archivo handoff, actualizaciones de memoria, extracción de lecciones, reflexión (qué salió mal, qué mejorar) |

### Calidad

| Habilidad | Función |
|-----------|---------|
| [project-check](../project-check/) | Escanea el proyecto existente en 4 dimensiones: Infraestructura, Seguridad, Calidad, Harness. Brechas ordenadas por severidad |
| [collab-audit](../collab-audit/) | Auditoría de colaboración AI en 14 secciones — analiza patrones de trabajo reales (no encuestas) para generar perfil conductual, puntos ciegos y dirección de crecimiento |

### Operaciones

| Habilidad | Función |
|-----------|---------|
| [skill-ops](../skill-ops/) | **Nuevo.** Hub de operaciones de habilidades/agentes — snapshot/rollback + salud de uso + seguimiento de invocaciones, 3 modos |
| [project-overview](../project-overview/) | **Nuevo.** Genera un mapa determinista del estado entre proyectos a partir de los handoffs de sesión de los proyectos registrados |

### Gobernanza

| Habilidad | Función |
|-----------|---------|
| [full-audit](../full-audit/) | **Nuevo.** Auditoría exhaustiva de un área completa (código/documentación/skills/memoria/configuración) — método de dos capas: barrido determinista + revisión de contenido, kill-test anti-falsos-positivos, mapa de cobertura persistente |
| [integration-intake](../integration-intake/) | **Nuevo.** Puerta de selección de 5 puntos para adoptar patrones externos (skills/agentes/reglas/plugins/MCP) — verificación de redundancia contra tus activos existentes + verificación de procedencia/inyección para contenido ejecutable importado |
| [clean-room](../clean-room/) | **Nuevo.** Recorta solicitudes con elementos de seguridad hacia un alcance seguro, ejecutado por un subagente de contexto completamente aislado — paso de verificación adversarial + registro de exclusión (descope ledger) |
| [eval-leakage-audit](../eval-leakage-audit/) | **Nuevo.** Audita si un eval/métrica/holdout realmente asegura una verdad de referencia externa independiente o es una autoconfirmación circular — taxonomía de 18 patrones. Solo lectura |
| [doc-drift](../doc-drift/) | **Nuevo.** Audita la memoria/documentación que Claude Code carga en el contexto (CLAUDE.md/MEMORY.md/skills/agents/commands) buscando afirmaciones desactualizadas, contradicciones mutuas y redacción riesgosa/ambigua — produce una lista de correcciones priorizada |

---

## Flujo del ciclo de vida

```
┌─────────────────── Configuración (1 vez) ──────────┐
│  /project-init  →  /setup                           │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────── Ciclo diario ───────────────────┐
│  /session-start                                      │
│       ↓                                              │
│  /scope → /freeze → /goal-lock → trabajo              │
│       → /stepback (en cualquier momento) → /code-autopsy → /pre-push│
│       ↓                                              │
│  /session-checkpoint                                 │
└──────────────────────────────────────────────────────┘
         ↓
┌─────────────────── Bajo demanda ───────────────────┐
│  /stepback         (reinicio de perspectiva — en cualquier momento) │
│  /project-check    (auditoría de salud)              │
│  /collab-audit     (diagnóstico conductual)          │
│  /integration-intake (antes de adoptar algo externo) │
│  /full-audit       (auditoría exhaustiva de un área) │
│  /clean-room       (aislar alcance seguro/inseguro)  │
│  /eval-leakage-audit (chequeo de lógica circular en evals) │
│  /doc-drift        (auditoría de drift del contexto cargado) │
└─────────────────────────────────────────────────────┘
```

---

## Instalación

### Opción A: Copiar habilidades (más simple)

```bash
# Instalar todas las habilidades
git clone https://github.com/AlexZio00/sovereign-skills.git
cd sovereign-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# O instalar una habilidad individual
cp -r goal-lock ~/.claude/skills/
```

### Opción B: Marketplace (sovereign-plugins)

Este repositorio es un marketplace de Claude Code. Regístrelo una vez para explorar e instalar habilidades:

```bash
# Agregar marketplace sovereign-plugins en Claude Code
# Configuración → Plugins → Agregar Marketplace → https://github.com/AlexZio00/sovereign-skills.git
```

Cada habilidad también incluye metadatos `.claude-plugin/plugin.json` independientes.

Escriba el comando de activación (ej: `/goal-lock`) en Claude Code para ejecutar la habilidad.

### Opción C: Codex / Cursor (npx)

Cada habilidad incluye `agents/openai.yaml`:

```bash
# Instalar habilidad para Codex
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent codex -g -y

# Instalar habilidad para Cursor
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent cursor -g -y

# Instalar para Claude Code (alternativa a la opción A)
npx skills add AlexZio00/sovereign-skills --skill goal-lock --agent claude-code -g -y
```

El contenido de SKILL.md es universal — funciona con cualquier LLM que lea instrucciones markdown.

### Requisitos

- **Claude Code**: CLI, app de escritorio o app web ([claude.ai/code](https://claude.ai/code))
- **Codex**: OpenAI Codex (soporte para `npx skills`)
- **Cursor**: Cursor IDE (soporte para plugin de habilidades)
- Directorio de habilidades: `~/.claude/skills/` (Claude Code) o ruta específica del agente
- `pre-push` requiere Perl (`scan_secrets.pl` incluido)

---

## Qué hay nuevo en v6.2

### Agregado
- **stepback** — Reinicio de perspectiva en un paso. Genera 1 pregunta de reencuadre abstracto (patrón step-back de DeepMind) + 3 comprobaciones rápidas (desvío de alcance, efectos secundarios, mejor enfoque) en menos de 10 líneas. Solo lectura, sin agentes, sin código. Use en cualquier momento durante el trabajo para verificar que está resolviendo el problema correcto al nivel correcto. Fuente: team-attention/hoyeon.

### Actualizado
- **code-autopsy** — Puertas de metadetección agregadas: métrica de límite CapCode para detectar manipulación de puntuación, detección CEF de errores falsos para evasión de restricciones.
- **collab-audit** — 13→14 secciones. Nueva Sección 12: Trayectoria del Nivel de Pensamiento (modelo de 5 niveles de Solicitante de Información a Diseñador de Pensamiento + seguimiento de cambio temporal + corrección de atribución de IA).
- **goal-lock** — Agregado Ralph Wiggum detección de finalización temprana (12º patrón de enmascaramiento) + trazabilidad de verificación en la etapa VERIFY (toda afirmación debe rastrearse hasta una llamada de herramienta real).
- **session-checkpoint** — Agregado autoverificación de claridad de entrega (2 preguntas de anclaje después de escribir la entrega).
- **session-start** — Agregado Prevención de Decadencia de Contexto (ventana deslizante para entradas de entrega antiguas).
- **pre-push** — Agregada Verificación de Cadena de Suministro de 3-IOC para dependencias recién agregadas.
- **scope** — Campo de Contraindicación agregado (condiciones donde el enfoque elegido NO es adecuado).
- **freeze** — Protocolo Thaw agregado (flujo de descongelación formal con verificación de radio de explosión, 3 advertencias de descongelación).
- **project-init** — Plantilla `.env.example` extendida (OAuth, servicios externos, secciones de monitoreo) + notas de línea base de seguridad.
- **project-check** — Seguimiento de Delta de Puntuación agregado (comparar resultados de escaneo actual vs anterior).
- **setup** — Protocolo de Rediseño agregado para fallos de prueba de violación de Tier 0 (escalada de 3 opciones).

---

## Qué hay nuevo en v6.1

### Agregado
- **code-autopsy** — Prompt de revisión de código cuantificado 12Q (Code Autopsy v7.0). 12 preguntas de análisis que abarcan desde el diseño hasta la observabilidad. Puntuación compuesta de 4 ejes (Security × 0.35 + Stability × 0.30 + Robustness × 0.20 + Operability × 0.15). Tabla de anclajes de severidad con fórmula ponderada. Veredicto de despliegue con límite duro CRITICAL. Puerta de Factualidad (autoverificación antes de reportar). Análisis de impacto entre archivos. Modo Rápido y Modo Diff. Respaldado por: Google eng-practices, Johnson et al. 2019, Parnas 1972. Funciona como prompt independiente en cualquier LLM — no es exclusivo de Claude Code.

---

## Qué hay nuevo en v6.0

### Agregado
- **goal-lock** — Motor de disciplina de agentes con ciclo PLAN→DO→VERIFY→FINALIZE→OUTPUT. Detecta 13 patrones de enmascaramiento de éxito (eliminación de pruebas, envoltura de mock, relajación de umbral, etc.). Modo Rápido (3 campos) para cambios pequeños, Modo Completo (7 campos) para todo lo demás.

### Fusionado
- `harness-init` + `team-init` → **setup** — Infraestructura y equipo de agentes en un flujo
- `brief` + `adr` → **scope** — Definición de alcance con capacidad ADR integrada
- `retro` → **session-checkpoint** — Retrospección es ahora Phase 1.7 Reflexion dentro de session-checkpoint

### Removido
- `token-audit` — Use `npx ccusage` directamente, o construya una habilidad ccusage a partir del patrón
- `adr` (independiente) — Absorbido en scope
- `retro` (independiente) — Absorbido en session-checkpoint

### Actualizado
- Todas las habilidades: Dominant Variable, Key Assumptions, Error Recovery, Safety Layers agregados
- Todas las habilidades: Scope Boundary con etiquetas de acción ([READ]/[WRITE]/[BASH]/[AGENT])
- `session-checkpoint`: Compresión Memento CoT, Reflexión, Registro de Invocación
- `pre-push`: Agrupamiento determinista de diff grande, Condiciones Discard If
- `collab-audit`: Indicadores de antipatrón, Key Assumptions

---

## Cobertura de Patrones de Diseño Agénico

17 de estas 20 habilidades (el conjunto original del ciclo de vida, las nuevas habilidades de gobernanza de v6.4, y las nuevas habilidades de auditoría de v6.5 — las nuevas habilidades de operaciones de v6.3 aún no están mapeadas aquí) implementan 17 de los 25 patrones de diseño agénico conocidos ([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| Patrón | Implementado por | Cómo |
|--------|------------------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | Cadena de ciclo de vida completo |
| **Parallel Execution** | pre-push | Agentes paralelos de revisión de código AI |
| **Loop (Retry)** | goal-lock | VERIFY falla → reingreso a PLAN, con límites |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | code-reviewer + security-reviewer independientes; revisión estructurada 12Q; pase de revisores en abanico de la Fase 2 de full-audit; eval-leakage-audit critica si un eval asegura una verdad de referencia independiente o es autoconfirmación circular |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE pasa |
| **Coordinator/Router** | setup | Generación de reglas de enrutamiento de agentes |
| **Plan-and-Execute** | goal-lock, scope | Plan revisable antes de ejecución |
| **ReAct** | project-check | Investigar → puntuar → recomendar ruta |
| **Reflexion** | session-checkpoint | Phase 1.7: analizar fallos → lecciones para próxima sesión |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES, Critical/High bloquea push; puerta de cribado de 5 puntos de integration-intake antes de adoptar |
| **Custom Logic** | pre-push | Escaneo determinista de secretos (Perl) + revisión AI |
| **Event-Driven** | session-start | Se dispara al abrir sesión, carga estado anterior |
| **Guardrails/Safety** | goal-lock, clean-room | 13 patrones de enmascaramiento de éxito detectados; clean-room aísla el alcance relacionado con seguridad en una ejecución de subagente separada |
| **Memory Management** | session-checkpoint, doc-drift | Archivo handoff + actualizaciones de memoria + extracción de lecciones; doc-drift audita la memoria/documentación cargada en el contexto en busca de afirmaciones desactualizadas, contradicciones y redacción riesgosa |
| **Goal Setting** | goal-lock | Hoja de entrada GOAL + DONE EVIDENCE |
| **Step-Back Abstraction** | stepback | DeepMind step-back: concreto → principio abstracto |

---

## Principios de diseño

1. **Entrevista sobre plantilla** — Las habilidades hacen preguntas y generan contenido completo, no esqueletos vacíos
2. **Verificación sobre confianza** — La evidencia de completitud debe ejecutarse, no asumirse. "Debería pasar" no es verificación
3. **Alcance antes del código** — Definir IN/OUT/criterios de salida antes de tocar archivos. Congelar lo que no se cambia
4. **Reporte honesto** — Etiquetas WORKING / PARTIAL / BROKEN. Sin fallos silenciosos, sin engaño con mocks
5. **Continuidad de sesión** — Comenzar con handoff, terminar con checkpoint. El contexto sobrevive entre sesiones

---

## Cómo se conectan las habilidades

Las habilidades declaran relaciones mediante `see_also` (relacionadas) y `not_for` (guardarraíles de mal uso) en su frontmatter. Relaciones clave:

| Habilidad | Se conecta con | Relación |
|-----------|-----------------|----------|
| `scope` | `goal-lock`, `freeze` | scope define qué construir; freeze bloquea la zona editable; goal-lock fuerza el ciclo de ejecución |
| `freeze` | `scope`, `goal-lock` | freeze es el bloqueo manual de zona que acompaña a la planificación de scope y la aplicación del ciclo de goal-lock |
| `goal-lock` | `scope`, `freeze` | goal-lock es la capa de disciplina en tiempo de ejecución que opera dentro de los límites que scope/freeze establecen |
| `stepback` | `next-action` | stepback verifica la dirección ("¿estoy resolviendo el problema correcto?"), next-action recomienda qué hacer ("¿qué sigue según impacto?") |
| `next-action` | `session-start`, `stepback` | next-action lee el estado actual para dar recomendaciones; session-start restaura el estado de la sesión anterior |
| `session-start` | `session-checkpoint` | par de ciclo de vida — abre y cierra una sesión |
| `session-checkpoint` | `session-start`, `setup` | cierra una sesión; setup abre un nuevo proyecto |
| `code-autopsy` | `pre-push` | code-autopsy es una revisión 12Q profunda bajo demanda; pre-push ejecuta un pipeline automatizado más rápido antes de cada push |
| `skill-ops` | `project-overview` | skill-ops gestiona el ciclo de vida de habilidades/agentes (snapshot/rollback/uso); project-overview agrega el estado entre múltiples proyectos |
| `integration-intake` | `full-audit` | integration-intake filtra una única decisión de adopción externa; full-audit barre un área entera (incluyendo tu inventario existente de habilidades/agentes) buscando drift o brechas |
| `full-audit` | `code-autopsy`, `project-check` | full-audit es un barrido más amplio multi-área con mapa de cobertura persistente; code-autopsy sigue siendo por archivo/12Q, project-check sigue siendo una puntuación de 4 dimensiones |
| `clean-room` | `goal-lock` | clean-room se activa cuando el alcance de una tarea mezcla material relacionado con seguridad y trabajo seguro a mitad de ejecución; goal-lock es el bucle PLAN→DO→VERIFY que interrumpe |
| `doc-drift` | `full-audit` | doc-drift solo audita la memoria/documentación cargada en el contexto (CLAUDE.md/MEMORY.md/skills/agents) buscando drift y contradicciones; full-audit barre un área entera con un mapa de cobertura |
| `eval-leakage-audit` | `full-audit`, `code-autopsy` | eval-leakage-audit comprueba si un eval/métrica/holdout es circular (integridad de la medición); full-audit y code-autopsy revisan código/áreas, no la independencia del eval |

Diagrama (flechas = "entrega a" / "informa a"):

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (en cualquier momento, cualquier etapa)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (lee el estado y recomienda)
                                   │
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift
                (gobernanza bajo demanda, cualquier etapa)
```

---

## Licencia

MIT — ver [LICENSE](../LICENSE).

## Contribuir

Issues y PRs son bienvenidos. Si crea una habilidad que encaje en el ciclo de vida, abra un PR.

## Contacto

DM a [@AlexZio00](https://x.com/AlexZio00) para desarrollo de habilidades personalizadas.
