[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | 🌐 **Español**

# sovereign-skills v6.4

18 habilidades para el ciclo de vida completo de proyectos con Claude Code — desde la configuración hasta el flujo de trabajo diario, revisión de código, gestión de sesiones y gobernanza. Cada habilidad funciona de forma independiente; la secuencia completa cubre todas las etapas.

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
| [code-autopsy](../code-autopsy/) | **Actualizado v7.1.** Revisión de código cuantificada 12Q — puntuación de 4 ejes (Security/Stability/Robustness/Operability), anclajes de severidad, veredicto de despliegue (SHIP/FIX/RISKY/BLOCK), gate de factualidad, detección de gaming CapCode, detección de errores fabricados CEF. Funciona como prompt independiente en cualquier LLM |

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

12 de estas 18 habilidades (el conjunto original del ciclo de vida — las nuevas habilidades de operaciones de v6.3 y las nuevas habilidades de gobernanza de v6.4 aún no están mapeadas aquí) implementan 17 de los 25 patrones de diseño agénico conocidos ([Gulli 2026](https://books.google.com/books/about/Agentic_Design_Patterns.html?id=QqR20QEACAAJ), [Sairahul 2026](https://x.com/sairahul1/status/2069045570556383464)):

| Patrón | Implementado por | Cómo |
|--------|------------------|------|
| **Sequential Pipeline** | session-start → scope → goal-lock → pre-push → checkpoint | Cadena de ciclo de vida completo |
| **Parallel Execution** | pre-push | Agentes paralelos de revisión de código AI |
| **Loop (Retry)** | goal-lock | VERIFY falla → reingreso a PLAN, con límites |
| **Review & Critique** | pre-push, code-autopsy | code-reviewer + security-reviewer independientes; revisión estructurada 12Q |
| **Iterative Refinement** | goal-lock | PLAN→DO→VERIFY→FINALIZE until DONE EVIDENCE pasa |
| **Coordinator/Router** | setup | Generación de reglas de enrutamiento de agentes |
| **Plan-and-Execute** | goal-lock, scope | Plan revisable antes de ejecución |
| **ReAct** | project-check | Investigar → puntuar → recomendar ruta |
| **Reflexion** | session-checkpoint | Phase 1.7: analizar fallos → lecciones para próxima sesión |
| **Human-in-the-Loop** | goal-lock, pre-push | STOP RULES, Critical/High bloquea push |
| **Custom Logic** | pre-push | Escaneo determinista de secretos (Perl) + revisión AI |
| **Event-Driven** | session-start | Se dispara al abrir sesión, carga estado anterior |
| **Guardrails/Safety** | goal-lock | 13 patrones de enmascaramiento de éxito detectados |
| **Memory Management** | session-checkpoint | Archivo handoff + actualizaciones de memoria + extracción de lecciones |
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

Diagrama (flechas = "entrega a" / "informa a"):

```
setup ──> scope ──> freeze ──> goal-lock ──> pre-push
                                   │
                                stepback (en cualquier momento, cualquier etapa)
                                   │
session-start <──> session-checkpoint
                                   │
                            next-action (lee el estado y recomienda)
```

---

## Licencia

MIT — ver [LICENSE](../LICENSE).

## Contribuir

Issues y PRs son bienvenidos. Si crea una habilidad que encaje en el ciclo de vida, abra un PR.

## Contacto

DM a [@AlexZio00](https://x.com/AlexZio00) para desarrollo de habilidades personalizadas.
