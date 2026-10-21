[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | 🌐 **Español**

# sovereign-skills v6.5.15

22 habilidades para el ciclo de vida completo de proyectos con Claude Code — desde la configuración hasta el flujo de trabajo diario, revisión de código, gestión de sesiones y gobernanza. Cada habilidad funciona de forma independiente; la secuencia completa cubre todas las etapas.

> **Cambios en v6.5.15:** Dos habilidades nuevas — `ssot-audit` (encuentra todas las copias de un mismo dato y señala la fuente de verdad) y `skill-trigger-auditor` (comprueba que las habilidades y los comandos se enruten correctamente). Correcciones de errores: `pre-push` ya no omite las pruebas ni el lint cuando se hace commit primero y push después; `project-check` ahora detecta claves de API con guiones (`sk-ant-…`, `sk-proj-…`); los ejemplos de hooks de `setup` ya no necesitan `bash` + `jq`, así que funcionan en Windows. Mejoras en otras habilidades: `code-autopsy` marca cada hallazgo como NEW o PRE-EXISTING e indica su nivel de evidencia; las habilidades de sesión señalan los elementos del handoff cuya fecha ya pasó; `integration-intake` consulta sus propios veredictos anteriores antes de revisar de nuevo un repositorio. Las 22 habilidades también pasaron por una auditoría de lectura completa: los scripts incluidos se encuentran desde cualquier ubicación de instalación (`${CLAUDE_SKILL_DIR}`), funcionan con Python 3.9+ y en macOS, los agentes externos opcionales están etiquetados con alternativas, y los formatos de archivo compartidos están documentados en [docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md). Ver [CHANGELOG.md](../CHANGELOG.md).

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
/collab-audit       →  Diagnóstico de colaboración AI en 14 secciones a partir de tus patrones de trabajo
```

**Gobernanza y auditorías (según necesidad):**
```
/integration-intake →  antes de adoptar una habilidad/agente/regla/plugin externo — filtro de 5 puntos
/full-audit         →  auditoría exhaustiva de un área completa (código/docs/habilidades/memoria/config) con mapa de cobertura
/clean-room         →  cuando una tarea mezcla material relacionado con seguridad y trabajo genuinamente seguro
/eval-leakage-audit →  antes de confiar en un eval/métrica/holdout — comprobar autoconfirmación circular
/doc-drift          →  auditar el contexto cargado (CLAUDE.md/MEMORY.md/skills) por redacción desactualizada/contradictoria
/ssot-audit         →  un dato repetido en muchos archivos — encontrar la fuente de verdad y luego consolidar
```

**Si escribe sus propias habilidades:**
```
/skill-trigger-auditor →  antes de cambiar la descripción de una habilidad — detectar colisiones de enrutamiento y activaciones erróneas
/skill-ops             →  snapshot/rollback de una habilidad antes de editarla, ver qué habilidades se usan de verdad
/project-overview      →  un solo mapa de estado para varios proyectos
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
| [scope](../scope/) | Definir IN/OUT/criterios de salida antes de implementar. Modo Quick (3 preguntas) o modo Full (especificación por capas). El modo Full incluye `coverage_check.py` (requisito ↔ tarea) |
| [freeze](../freeze/) | Declarar la zona editable — todo lo demás queda congelado. Previene la expansión del alcance durante la implementación |
| [goal-lock](../goal-lock/) | Motor de disciplina de agentes — bloquea el objetivo, fuerza el ciclo PLAN→DO→VERIFY→FINALIZE→OUTPUT, detecta 16 patrones de enmascaramiento de éxito |
| [pre-push](../pre-push/) | Pipeline pre-push obligatorio — escaneo de secretos (14 patrones), build/test, lint, revisión de código AI en paralelo. Comprueba lo que el push realmente lleva (cambios en staging + commits pendientes de enviar). Bloquea push ante hallazgos Critical/High |

### Cambio de perspectiva

| Habilidad | Función |
|-----------|---------|
| [stepback](../stepback/) | Reinicio de perspectiva en un paso — 1 pregunta de reencuadre abstracto + 3 verificaciones rápidas (desvío de alcance, efectos secundarios, mejor enfoque) y un veredicto de continuar/parar, en menos de 10 líneas. Usar en cualquier momento durante el trabajo |
| [next-action](../next-action/) | Lee handoff/git/lessons/STATE y propone las 3 acciones principales según impacto. Solo propone, nunca ejecuta. Usar en cualquier momento |

### Gestión de sesiones

| Habilidad | Función |
|-----------|---------|
| [session-start](../session-start/) | Carga el handoff de la sesión anterior, revisa lecciones aprendidas, health check, señal de "listo" con acción prioritaria. Señala los elementos del handoff cuya fecha ya pasó |
| [session-checkpoint](../session-checkpoint/) | Guarda el contexto de sesión antes del compact — archivo handoff, actualizaciones de memoria, extracción de lecciones, reflexión (qué salió mal, qué mejorar). Mantiene los elementos con fecha futura en una lista aparte, "Scheduled checks" |

### Revisión de código

| Habilidad | Función |
|-----------|---------|
| [code-autopsy](../code-autopsy/) | Revisión de código cuantificada 12Q (v7.3) — puntuación de 4 ejes (Security/Stability/Robustness/Operability), anclajes de severidad, veredicto de despliegue (SHIP/FIX/RISKY/BLOCK), gate de factualidad. Cada hallazgo se marca como NEW o PRE-EXISTING y lleva un nivel de evidencia. Respaldada por evidencia empírica (Johnson 2019, Parnas 1972). Funciona como prompt independiente en cualquier LLM |

### Calidad

| Habilidad | Función |
|-----------|---------|
| [project-check](../project-check/) | Escanea el proyecto existente en 4 dimensiones: Infraestructura, Seguridad, Calidad, Harness. Brechas ordenadas por severidad |
| [collab-audit](../collab-audit/) | Auditoría de colaboración AI en 14 secciones — analiza patrones de trabajo reales (no encuestas) para generar perfil conductual, puntos ciegos y dirección de crecimiento. `extract_session_meta.py` genera los datos de sesión que necesita |

### Operaciones

| Habilidad | Función |
|-----------|---------|
| [skill-ops](../skill-ops/) | Hub de operaciones de habilidades/agentes — snapshot/rollback + salud de uso + seguimiento de invocaciones + puntuación de calidad, 4 modos. Incluye `skill_snapshot.py` y `skill_health_bucket.py` |
| [project-overview](../project-overview/) | Genera un mapa determinista del estado entre proyectos a partir de los handoffs de sesión de los proyectos registrados, e informa de los snapshots con más de 7 días |
| [skill-trigger-auditor](../skill-trigger-auditor/) | **Nuevo en v6.5.15.** Audita el enrutamiento de habilidades, agentes y comandos slash en busca de colisiones y activaciones erróneas, y condiciona los cambios de descripción a pruebas de activación con un conjunto de reserva (holdout). Una sonda opcional mide llamadas reales a la herramienta Skill |

### Gobernanza

| Habilidad | Función |
|-----------|---------|
| [full-audit](../full-audit/) | Auditoría exhaustiva de un área completa (código/documentación/skills/memoria/configuración) — método de dos capas: barrido determinista + revisión de contenido, kill-test anti-falsos-positivos, canarios sembrados, mapa de cobertura persistente |
| [integration-intake](../integration-intake/) | Puerta de selección de 5 puntos para adoptar patrones externos (skills/agentes/reglas/plugins/MCP) — verificación de redundancia contra tus activos existentes, verificación de procedencia/inyección para contenido ejecutable importado, una línea de licencia y consulta en un registro de veredictos anteriores |
| [clean-room](../clean-room/) | Recorta solicitudes con elementos de seguridad hacia un alcance seguro, ejecutado por un subagente de contexto completamente aislado — paso de verificación adversarial + registro de exclusión (descope ledger) |
| [eval-leakage-audit](../eval-leakage-audit/) | Audita si un eval/métrica/holdout realmente asegura una verdad de referencia externa independiente o es una autoconfirmación circular — taxonomía de 28 patrones, dos casos de referencia (golden). Solo lectura |
| [doc-drift](../doc-drift/) | Audita la memoria/documentación que Claude Code carga en el contexto (CLAUDE.md/MEMORY.md/skills/agents/commands) buscando afirmaciones desactualizadas, contradicciones mutuas y redacción riesgosa/ambigua — produce una lista de correcciones priorizada |
| [ssot-audit](../ssot-audit/) | **Nuevo en v6.5.15.** Encuentra todas las copias de un dato, valor o decisión en un repositorio o carpeta de notas, señala la fuente de verdad (solo lectura) y consolida los duplicados únicamente después de que usted lo apruebe |

---

## Flujo del ciclo de vida

```
┌─────────────────── Setup (once) ────────────────────┐
│  /project-init  →  /setup                           │
└─────────────────────────────────────────────────────┘
         ↓
┌──────────────────── Daily Loop ─────────────────────┐
│  /session-start                                     │
│       ↓                                             │
│  /scope → /freeze → /goal-lock → work               │
│       → /stepback (anytime) → /code-autopsy         │
│       → /pre-push                                   │
│       ↓                                             │
│  /session-checkpoint                                │
└─────────────────────────────────────────────────────┘
         ↓
┌───────────────────── On Demand ─────────────────────┐
│  /stepback         (perspective reset — anytime)    │
│  /next-action      (top-3 next actions from state)  │
│  /project-check    (health audit)                   │
│  /code-autopsy     (12Q code review — any LLM)      │
│  /collab-audit     (behavioral diagnostic)          │
│  /integration-intake (before adopting external work)│
│  /full-audit       (exhaustive area audit)          │
│  /clean-room       (safety-adjacent scope carve-out)│
│  /eval-leakage-audit (eval circular-logic check)    │
│  /doc-drift        (loaded-context drift audit)     │
│  /ssot-audit       (one fact, many copies)          │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────── Skill authors / multi-project ───────────┐
│  /skill-ops        (snapshot, rollback, usage)      │
│  /skill-trigger-auditor (routing collisions)        │
│  /project-overview (cross-project status map)       │
└─────────────────────────────────────────────────────┘
```

---

## Instalación

### Opción A: Copiar habilidades (más simple)

Cada habilidad es un directorio independiente con un archivo `SKILL.md`. Copie las que quiera:

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

Las habilidades se invocan escribiendo el comando de activación (ej: `/goal-lock`) en Claude Code. Claude lee el SKILL.md y sigue las instrucciones.

### Opción C: Codex

Codex descubre habilidades escaneando `.agents/skills/<nombre-habilidad>/SKILL.md` a nivel de repositorio, usuario (`$HOME/.agents/skills`), administrador y sistema — no se necesita una definición de agente aparte. Instale una habilidad para Codex de la misma forma que para Claude Code, solo que bajo la ruta `.agents/skills/`:

```bash
# Nivel usuario (disponible en todos los proyectos)
cp -r goal-lock ~/.agents/skills/goal-lock/

# Nivel repositorio (solo este proyecto)
cp -r goal-lock .agents/skills/goal-lock/
```

Cada habilidad también incluye de forma **opcional** `agents/openai.yaml` — metadatos de UI/política para la app de escritorio de ChatGPT (nombre visible, descripción, ícono/color de marca, y el flag `allow_implicit_invocation`, `true` por defecto). No es necesario para que Codex encuentre o ejecute la habilidad; cópielo junto con `SKILL.md` solo si desea aplicar esos metadatos:

```bash
cp -r goal-lock/agents .agents/skills/goal-lock/agents/
```

Consulte la [documentación oficial de habilidades de Codex](https://learn.chatgpt.com/docs/build-skills) para conocer la especificación completa de descubrimiento y metadatos.

### Opción D: Cursor / Otros agentes

El contenido de SKILL.md es markdown universal — funciona con cualquier LLM que lea instrucciones markdown. Copie `SKILL.md` en la ruta de instrucciones de su agente.

### Requisitos

- **Claude Code**: CLI, app de escritorio o app web ([claude.ai/code](https://claude.ai/code))
- **Codex**: OpenAI Codex — lee `SKILL.md` directamente desde `.agents/skills/`; `agents/openai.yaml` son metadatos de UI opcionales
- **Cursor / Otros**: cualquier agente que lea instrucciones markdown
- Directorio de habilidades: `~/.claude/skills/` (Claude Code) o ruta específica del agente
- Python 3.9+ para los scripts auxiliares incluidos (`scripts/*.py` dentro de varias habilidades). Las habilidades los llaman como `${CLAUDE_SKILL_DIR}/scripts/<name>.py`, y Claude Code rellena ese valor con la carpeta de la propia habilidad; en otros agentes, sustitúyelo por la carpeta donde instalaste la habilidad. Cuando un script no puede ejecutarse, cada habilidad indica si recurre a un paso manual o se detiene
- `pre-push` incluye tanto `scan_secrets.py` (preferido) como `scan_secrets.pl` (respaldo Perl). Opcional: `ruff` (lint de las líneas modificadas) y `gitleaks` (segundo motor de escaneo de secretos, solo avisa)

### Archivos que las habilidades de sesión leen y escriben

`session-start`, `session-checkpoint`, `next-action`, `project-overview`, `skill-ops` y `collab-audit` comparten unos pocos archivos de texto plano: un handoff de sesión, `tasks/lessons.md`, `~/.claude/STATE.md`, `memory/MEMORY.md`, un registro de contexto y un registro de invocaciones. Ninguno es obligatorio: si falta el archivo, la habilidad omite ese paso. Formatos: [docs/FILE-CONVENTIONS.md](FILE-CONVENTIONS.md).

### Agentes y habilidades opcionales que no se incluyen aquí

Algunas habilidades pueden delegar trabajo a agentes o habilidades que este repositorio **no** incluye. Cada mención en un SKILL.md está marcada como opcional y tiene una alternativa, así que nada se rompe si faltan:

| Nombre | Lo usa | Sin él |
|--------|--------|--------|
| `code-reviewer`, `security-reviewer`, `database-reviewer`, `build-error-resolver` | pre-push | `/setup` puede generar estos agentes; si no, pre-push ejecuta una revisión en línea (code-autopsy FAST MODE) y marca los pasos de agente como SKIPPED |
| `refactor-cleaner` | pre-push | se omite el paso |
| `doubt-reviewer` | scope (modo Full), goal-lock | un subagente de propósito general con un prompt adversarial, o SKIPPED en el informe |
| `verification`, `brainstorming`, `check-harness`, `memory-dream`, `forge` | varias notas de see-also / enrutamiento | solo referencias — la habilidad funciona sin ellos |

---

## Cobertura de Patrones de Diseño Agénico

Las habilidades corresponden a 18 patrones de diseño agénico de los catálogos publicados ([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| Patrón | Implementado por | Cómo |
|--------|------------------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | Cadena de ciclo de vida completo |
| **Parallel Execution** | pre-push | Agentes paralelos de revisión de código AI |
| **Loop (Retry)** | goal-lock | VERIFY falla → reingreso a PLAN, con límites |
| **Review & Critique** | pre-push, code-autopsy, full-audit, eval-leakage-audit | subagentes revisores independientes (opcionales — ver arriba) o una revisión en línea; revisión estructurada 12Q; pase de revisores en abanico de la Fase 2 de full-audit; eval-leakage-audit critica si un eval asegura una verdad de referencia independiente o es autoconfirmación circular |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE pasa |
| **Coordinator/Router** | setup | Generación de reglas de enrutamiento de agentes |
| **Plan-and-Execute** | goal-lock, scope | Plan revisable antes de ejecución |
| **ReAct** | project-check | Investigar → puntuar → recomendar ruta |
| **Reflexion** | session-checkpoint | Phase 1.7: analizar fallos → lecciones para próxima sesión |
| **Human-in-the-Loop** | goal-lock, pre-push, integration-intake | STOP RULES, Critical/High bloquea push; puerta de cribado de 5 puntos de integration-intake antes de adoptar |
| **Custom Logic** | pre-push | Escaneo determinista de secretos (Python, respaldo Perl) + revisión AI |
| **Event-Driven** | session-start | Se dispara al abrir sesión, carga estado anterior |
| **Guardrails/Safety** | goal-lock, clean-room | 16 patrones de enmascaramiento de éxito detectados; clean-room aísla el alcance relacionado con seguridad en una ejecución de subagente separada |
| **Memory Management** | session-checkpoint, doc-drift | Archivo handoff + actualizaciones de memoria + extracción de lecciones; doc-drift audita la memoria/documentación cargada en el contexto en busca de afirmaciones desactualizadas, contradicciones y redacción riesgosa |
| **Goal Setting** | goal-lock | Hoja de entrada GOAL + DONE EVIDENCE |
| **Step-Back Abstraction** | stepback | DeepMind step-back: concreto → principio abstracto |
| **Prioritization** | next-action | Ordena por impacto las acciones candidatas obtenidas de handoff/git/lessons/STATE |
| **Evaluation & Monitoring** | skill-ops, skill-trigger-auditor, project-overview | Salud de uso por habilidad; precisión/exhaustividad del enrutamiento sobre prompts de reserva (holdout); informe de snapshots obsoletos entre proyectos |

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
| `ssot-audit` | `doc-drift`, `full-audit` | ssot-audit sigue un mismo dato a través de varios archivos y elige la fuente de verdad; doc-drift busca drift en el contexto cargado; full-audit barre un área entera |
| `skill-trigger-auditor` | `skill-ops`, `doc-drift` | skill-trigger-auditor comprueba si las habilidades se activan con los prompts correctos; skill-ops registra si se usan y las revierte; doc-drift revisa su texto en busca de afirmaciones desactualizadas |
| `project-check` | `setup`, `collab-audit` | project-check puntúa la configuración de un repositorio y lista las brechas (setup las rellena); collab-audit examina cómo trabaja usted con la AI, no el repositorio |

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
    integration-intake / full-audit / clean-room / eval-leakage-audit / doc-drift / ssot-audit
                (gobernanza y auditorías bajo demanda, cualquier etapa)
                                   │
         skill-ops / skill-trigger-auditor / project-overview
                 (para autores de habilidades y configuraciones multiproyecto)
```

---

## Changelog

Consulte [CHANGELOG.md](../CHANGELOG.md) para el historial completo de versiones (v3.0 → la más reciente).

## Licencia

MIT — ver [LICENSE](../LICENSE).

## Contribuir

Issues y PRs son bienvenidos. Si crea una habilidad que encaje en el ciclo de vida, abra un PR.

## Contacto

DM a [@AlexZio00](https://x.com/AlexZio00) para desarrollo de habilidades personalizadas.
