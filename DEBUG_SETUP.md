# ✅ Debug Configuration Setup Complete

## 📋 Resumen

Se ha configurado completamente VS Code para debuggear el monorepo en modo debug con soporte para:

- ✅ Backend (FastAPI) - Python Debugger (debugpy)
- ✅ Web (Next.js) - Node debugger + Chrome DevTools
- ✅ Mobile (Expo) - Node debugger
- ✅ Tests (Backend) - Pytest debugging
- ✅ Configuraciones combinadas (Compounds)

## 📁 Archivos Creados/Modificados

### `.vscode/settings.json` ✨ ACTUALIZADO
```json
{
  // Python Debugging & Testing
  "python.debugging.enabled": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["apps/backend/tests", "-v"],
  
  // Type Checking
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.extraPaths": ["${workspaceFolder}/apps/backend"],
  
  // TypeScript/Node
  "debug.node.showUseWasmCommand": true,
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

### `.vscode/launch.json` ✨ NUEVO
**Configuraciones disponibles:**
1. **Backend (FastAPI)** - Debug con uvicorn + reload
2. **Backend Tests** - Pytest debugging
3. **Backend Test Single** - Debuggear test específico
4. **Web (Next.js Dev)** - Next.js dev server
5. **Web Build** - Debug del build
6. **Attach to Chrome (Web)** - Debugging en navegador
7. **Mobile (Expo)** - Expo debugging

**Configuraciones Combinadas (Compounds):**
- Backend + Web
- Backend + Web + Mobile

### `.vscode/tasks.json` ✨ NUEVO
**Tareas Disponibles (Ctrl+Shift+B):**

#### Docker
- Docker: Start Infrastructure
- Docker: Stop Infrastructure

#### Setup
- Backend: Install Dependencies
- Web: Install Dependencies
- Mobile: Install Dependencies

#### Backend
- Backend: Run Migrations
- Backend: Run Linter (Ruff)
- Backend: Format Code (Black)

#### Web
- Web: ESLint

#### General
- All: Pre-commit Hooks
- All: Start Development (Monorepo)

### `.vscode/extensions.json` ✨ NUEVO
Extensiones recomendadas para el monorepo:
- Python Debugger (debugpy)
- Python, Pylance
- Black Formatter, Ruff
- ESLint, Prettier
- TypeScript Next
- Tailwind CSS
- GitLens, Git Graph
- SonarLint

### `.vscode/debug-guide.md` ✨ NUEVO
Guía completa (en `.vscode/debug-guide.md`) con:
- Cómo debuggear cada app
- Breakpoints y condicionales
- Troubleshooting
- Atajos de teclado
- Workflow recomendado

### `.gitignore` ✨ ACTUALIZADO
Ahora permite compartir archivos de configuración .vscode:
```
.vscode/
!.vscode/settings.json
!.vscode/launch.json
!.vscode/tasks.json
!.vscode/extensions.json
!.vscode/debug-guide.md
```

## 🚀 Cómo Usar

### Quick Start - Backend
```
1. Ctrl+Shift+D (Abre Run and Debug)
2. Selector: "Backend (FastAPI)"
3. F5 (Start Debug)
✅ Backend corre en http://localhost:8000
```

### Quick Start - Web
```
1. Ctrl+Shift+D
2. Selector: "Web (Next.js Dev)"
3. F5
✅ Web corre en http://localhost:3000
```

### Quick Start - Full Stack
```
1. Ctrl+Shift+D
2. Selector: "Backend + Web"
3. F5
✅ Ambos servicios inician automáticamente
```

### Ejecutar Tareas
```
1. Ctrl+Shift+B (Run Task)
2. Elige tarea: ej "Docker: Start Infrastructure"
3. Enter
```

## 🔍 Debugging Features

### Breakpoints
- F9 para toggle breakpoint
- Clic derecho → "Edit Breakpoint" para condicionales

### Variables Watch
- Agrega expresiones custom en panel Watch
- Inspecciona valores en tiempo real

### Call Stack
- Ver cadena de funciones que llevó al breakpoint

### Debug Console
- Ejecutar expresiones Python/JavaScript en vivo
- Acceso a variables locales y globales

## ⚡ Atajos Principales

| Atajo | Acción |
|-------|--------|
| F5 | Iniciar/Continuar |
| F9 | Toggle Breakpoint |
| F10 | Step Over |
| F11 | Step Into |
| Shift+F11 | Step Out |
| Ctrl+Shift+D | Debug View |
| Ctrl+Shift+B | Run Task |
| Ctrl+Shift+P | Paleta Comandos |

## 📝 Próximos Pasos

1. **Instalar extensiones recomendadas:**
   - VS Code mostrará notificación automáticamente
   - O: Ctrl+Shift+P → "Extensions: Show Recommended"

2. **Probar Debug Backend:**
   ```
   F5 → "Backend (FastAPI)" → Abre http://localhost:8000/health
   ```

3. **Probar Debug Web:**
   ```
   F5 → "Web (Next.js Dev)" → Abre http://localhost:3000
   ```

4. **Leer debug-guide.md completo:**
   - `.vscode/debug-guide.md` tiene guía detallada
   - Troubleshooting y workflows avanzados

## 🐛 Comando para Debuggear Rápidamente

```bash
# Terminal PowerShell
code .  # Abre VS Code
# Luego F5 → Elige configuración → Debug
```

## 📊 Estructura Configurada

```
.vscode/
├── settings.json       # Formatters, linters, Python testing
├── launch.json         # Todas las config de debug
├── tasks.json          # Tareas automatizadas
├── extensions.json     # Extensiones recomendadas
└── debug-guide.md      # Documentación (este archivo)
```

---

**¡Listo para debuggear el monorepo completo!** 🎯

Ejecuta `F5` y selecciona tu configuración preferida.
