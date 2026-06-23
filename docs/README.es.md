[English](../README.md) | [한국어](README.ko.md) | [日本語](README.ja.md) | [中文](README.zh.md) | 🌐 **Español**

# claude-code-skills v6.0

10 habilidades para el ciclo de vida completo de proyectos con Claude Code — desde la configuración hasta el flujo de trabajo diario y la gestión de sesiones. Cada habilidad funciona de forma independiente; la secuencia completa cubre todas las etapas.

> **Cambios en v6.0:** Consolidado de 13 a 10 habilidades. `harness-init` + `team-init` → `setup`. `brief` + `adr` → `scope`. `retro` absorbido en `session-checkpoint`. `token-audit` eliminado (usar `npx ccusage` CLI). Nuevo: `goal-lock` — motor de disciplina de agentes.

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
  /pre-push           antes de cada push (escaneo de secretos + revisión AI)
  /session-checkpoint al final de cada sesión
```

**Proyecto existente (5 min):**
```
/project-check      →  Puntuación en 4 dimensiones + lista de brechas por severidad
/collab-audit       →  Diagnóstico de colaboración AI en 13 secciones
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
| [goal-lock](../goal-lock/) | **Nuevo.** Motor de disciplina de agentes — bloquea el objetivo, fuerza el ciclo PLAN→DO→VERIFY→FINALIZE→OUTPUT, detecta 11 patrones de enmascaramiento de éxito |
| [pre-push](../pre-push/) | Pipeline pre-push obligatorio — escaneo de secretos (12 patrones), build/test, lint, revisión de código AI en paralelo. Bloquea push ante hallazgos Critical/High |

### Gestión de sesiones

| Habilidad | Función |
|-----------|---------|
| [session-start](../session-start/) | Carga el handoff de la sesión anterior, revisa lecciones aprendidas, health check, señal de "listo" con acción prioritaria |
| [session-checkpoint](../session-checkpoint/) | Guarda el contexto de sesión antes del compact — archivo handoff, actualizaciones de memoria, extracción de lecciones, reflexión (qué salió mal, qué mejorar) |

### Calidad

| Habilidad | Función |
|-----------|---------|
| [project-check](../project-check/) | Escanea el proyecto existente en 4 dimensiones: Infraestructura, Seguridad, Calidad, Harness. Brechas ordenadas por severidad |
| [collab-audit](../collab-audit/) | Auditoría de colaboración AI en 13 secciones — analiza patrones de trabajo reales (no encuestas) para generar perfil conductual, puntos ciegos y dirección de crecimiento |

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
│  /scope → /freeze → /goal-lock → trabajo → /pre-push│
│       ↓                                              │
│  /session-checkpoint                                 │
└──────────────────────────────────────────────────────┘
         ↓
┌─────────────────── Bajo demanda ───────────────────┐
│  /project-check    (auditoría de salud)              │
│  /collab-audit     (diagnóstico conductual)          │
└─────────────────────────────────────────────────────┘
```

---

## Instalación

### Opción A: Copiar habilidades (más simple)

```bash
# Instalar todas las habilidades
git clone https://github.com/AlexZio00/claude-code-skills.git
cd claude-code-skills
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.claude/skills/; done

# O instalar una habilidad individual
cp -r goal-lock ~/.claude/skills/
```

### Opción B: Marketplace (sovereign-plugins)

Este repositorio es un marketplace de Claude Code. Regístrelo una vez para explorar e instalar habilidades:

```bash
# Agregar marketplace sovereign-plugins en Claude Code
# Configuración → Plugins → Agregar Marketplace → https://github.com/AlexZio00/claude-code-skills.git
```

Cada habilidad también incluye metadatos `.claude-plugin/plugin.json` independientes.

Escriba el comando de activación (ej: `/goal-lock`) en Claude Code para ejecutar la habilidad.

### Requisitos

- [Claude Code](https://claude.ai/code) CLI, app de escritorio o app web
- Directorio de habilidades: `~/.claude/skills/` (creado automáticamente por Claude Code)
- `pre-push` requiere Perl (`scan_secrets.pl` incluido)

---

## Principios de diseño

1. **Entrevista sobre plantilla** — Las habilidades hacen preguntas y generan contenido completo, no esqueletos vacíos
2. **Verificación sobre confianza** — La evidencia de completitud debe ejecutarse, no asumirse. "Debería pasar" no es verificación
3. **Alcance antes del código** — Definir IN/OUT/criterios de salida antes de tocar archivos. Congelar lo que no se cambia
4. **Reporte honesto** — Etiquetas WORKING / PARTIAL / BROKEN. Sin fallos silenciosos, sin engaño con mocks
5. **Continuidad de sesión** — Comenzar con handoff, terminar con checkpoint. El contexto sobrevive entre sesiones

---

## Licencia

MIT — ver [LICENSE](../LICENSE).

## Contribuir

Issues y PRs son bienvenidos. Si crea una habilidad que encaje en el ciclo de vida, abra un PR.

## Contacto

DM a [@AlexZio00](https://x.com/AlexZio00) para desarrollo de habilidades personalizadas.
