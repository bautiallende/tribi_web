# Debug Guide - Tribi Monorepo

Esta guía explica cómo depurar cada aplicación en el monorepo usando VS Code.

## 🔧 Configuración Requerida

### Extensiones Necesarias

Se recomienda instalar las extensiones desde `.vscode/extensions.json`:

1. **Python Debugger** (ms-python.debugpy)
2. **Python** (ms-python.python)
3. **Pylance** (ms-python.vscode-pylance)
4. **Black Formatter** (ms-python.black-formatter)
5. **Ruff** (charliermarsh.ruff)
6. **ESLint** (dbaeumer.vscode-eslint)
7. **Prettier** (esbenp.prettier-vscode)

VS Code mostrará una notificación para instalarlas automáticamente.

### Antes de Iniciar Cualquier Debug

1. **Sincroniza variables nuevas:** copia los campos agregados en `.env.example` (p. ej. `JOB_ENABLED`, `SUPPORT_SLA_HOURS_*`, etc.) hacia tu `.env` para que los launchers carguen los valores correctos.
2. **Ejecuta migraciones:** `Ctrl+Shift+B → "Backend: Run Migrations"` (o `alembic upgrade head`) para crear las nuevas columnas/audit logs del CRM. Si cambiaste de rama, repite este paso.
3. **Scheduler opcional:** por defecto los modos de debug dejan `JOB_ENABLED=false` para evitar trabajos en 2º plano. Si querés probar los recordatorios/escalaciones basta con exportar `JOB_ENABLED=true` antes de lanzar el perfil **Backend (FastAPI)**.

### Estructura VS Code

```
.vscode/
├── settings.json      # Configuración del editor (formatters, linters)
├── launch.json        # Configuraciones de debugging
├── tasks.json         # Tareas automatizadas
├── extensions.json    # Extensiones recomendadas
└── debug-guide.md     # Este archivo
```

## 🚀 Modos de Debug

### 1. Backend (FastAPI)

#### Opción A: Debug con Hot Reload

1. Abre la paleta de comandos: `Ctrl+Shift+D`
2. Selecciona: **"Backend (FastAPI)"**
3. Presiona `F5` o haz clic en Play

```
✅ El backend inicia en http://localhost:8000
✅ Hot reload activado
✅ Breakpoints funcionan
✅ Variables inspeccionables
✅ Scheduler opcional (exporta JOB_ENABLED=true antes del launch si necesitás probar recordatorios)
```

#### Opción B: Debug de Tests

```
Selector: "Backend Tests" o "Backend Test Single"
```

Esto ejecuta pytest en modo debug permitiendo inspeccionar fallos en tests.

### 2. Web (Next.js)

#### Opción A: Debug Dev Server

1. Paleta: `Ctrl+Shift+D`
2. Selecciona: **"Web (Next.js Dev)"**
3. Presiona `F5`

```
✅ Next.js dev server inicia en http://localhost:3000
✅ Hot reload (Fast Refresh) activado
✅ Source maps habilitados
✅ Debugging desde VS Code funciona
```

#### Opción B: Attach to Chrome

1. Primero ejecuta: **"Web (Next.js Dev)"**
2. Abre Chrome y navega a http://localhost:3000
3. Luego ejecuta: **"Attach to Chrome (Web)"**
4. Ahora puedes poner breakpoints en TypeScript

```
✅ Debugging directo en el navegador
✅ Ver valores en tiempo real
✅ Inspeccionar DOM
```

### 3. Mobile (Expo)

#### Debug con Expo CLI

1. Paleta: `Ctrl+Shift+D`
2. Selecciona: **"Mobile (Expo)"**
3. Presiona `F5`

```
El launcher ejecuta `npm run start -- --tunnel` dentro de `apps/mobile` (carga `.env` de esa carpeta).

Aparecerá en terminal:
› Metro Bundler started
› Press 's' for Android
› Press 'i' for iOS
› Press 'w' for web
```

Luego en tu dispositivo:

- Abre Expo Go
- Escanea el QR mostrado en terminal

## 🔗 Configuraciones Combinadas (Compounds)

### Backend + Web

```
Selector: "Backend + Web"
```

Esto inicia ambos servicios automáticamente:

- Backend en puerto 8000
- Web en puerto 3000

**Uso típico:** desarrollo full-stack sin escribir comandos manuales.

### Backend + Web + Mobile

```
Selector: "Backend + Web + Mobile"
```

Inicia los tres servicios simultáneamente.

**Nota:** Los compounds también ejecutan automáticamente: `Docker: Start Infrastructure`

## ⚡ Tareas Disponibles

Accede a tareas con: `Ctrl+Shift+B` o desde la paleta: `>Tasks: Run Task`

### Docker

- **Docker: Start Infrastructure** - Inicia MySQL + MailHog
- **Docker: Stop Infrastructure** - Detiene servicios

### Setup

- **Backend: Install Dependencies** - pip install -r requirements.txt
- **Web: Install Dependencies** - npm install
- **Mobile: Install Dependencies** - npm install

### Backend

- **Backend: Run Migrations** - alembic upgrade head
- **Backend: Run Linter (Ruff)** - ruff check .
- **Backend: Format Code (Black)** - black .

### Web

- **Web: ESLint** - npm run lint

### General

- **All: Pre-commit Hooks** - pre-commit run --all-files
- **All: Start Development (Monorepo)** - make dev

## 🐛 Debugging Avanzado

### Breakpoints en Backend

```python
# apps/backend/app/main.py

@app.get("/health")
def read_health():
    status = "ok"
    # ← Pon un breakpoint aquí (F9)
    return {"status": status}
```

Cuando hagas GET a `/health`, el debug se pausará aquí.

### Breakpoints en Web

```typescript
// apps/web/app/health/page.tsx

async function getHealth() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/health`);
  // ← Breakpoint aquí (F9)
  return res.json();
}
```

### Variables Condicionales

Para debuggear solo bajo ciertas condiciones:

```python
# En Backend: breakpoint condicional
if not status:  # Solo para cuando sea False
    import pdb; pdb.set_trace()
```

O usando la UI:

1. Clic derecho en el breakpoint
2. Editar breakpoint
3. Agregar condición: `not status`

## 📊 Inspectores Disponibles

### Variables

- Locales: Variables en el scope actual
- Globales: Variables globales
- Watch: Agrega expresiones custom (ej: `len(items)`)

### Call Stack

- Ver el camino de función que llevó al breakpoint actual

### Debug Console

```
> Escribe Python/JS expresiones aquí
> app.get  # Backend: inspecciona FastAPI app
> document  # Web: inspecciona DOM
```

## 🚨 Troubleshooting

### "Module not found" en Backend

```bash
# Ejecuta primero:
Ctrl+Shift+B → "Backend: Install Dependencies"
```

### Next.js no compila

```bash
# Ejecuta:
Ctrl+Shift+B → "Web: Install Dependencies"
```

### "Cannot connect to Chrome"

```
1. Asegúrate que Next.js esté corriendo: "Web (Next.js Dev)"
2. Abre Chrome manualmente: http://localhost:3000
3. Luego ejecuta: "Attach to Chrome (Web)"
```

### Expo no carga

```bash
# El launcher ya usa --tunnel para dispositivos externos.
# Si seguís teniendo problemas:
expo start --clear --tunnel
```

### Breakpoints no se detienen

```
1. Verifica que "justMyCode" sea false para el tipo de debug
2. Recarga el archivo: Ctrl+Shift+P → "Developer: Reload Window"
3. Reinicia el debug: F5
```

## 💡 Atajos Útiles

| Atajo          | Acción                  |
| -------------- | ----------------------- |
| `F5`           | Iniciar/Continuar debug |
| `F9`           | Toggle breakpoint       |
| `F10`          | Step over               |
| `F11`          | Step into               |
| `Shift+F11`    | Step out                |
| `Ctrl+Shift+D` | Abrir debug             |
| `Ctrl+Shift+B` | Ejecutar tarea          |
| `Ctrl+Shift+P` | Paleta de comandos      |

## 📝 Workflow Recomendado

### Desarrollo Backend

```
1. Ctrl+Shift+D → "Backend (FastAPI)" → F5
2. Abre http://localhost:8000/health en navegador
3. Modifica código en VS Code
4. Auto-reload captura cambios
5. Refresh navegador si es necesario
```

### Desarrollo Web

```
1. Ctrl+Shift+D → "Web (Next.js Dev)" → F5
2. Abre http://localhost:3000 en navegador
3. Modifica código en VS Code
4. Fast Refresh automático
5. Dev tools abierto (F12)
```

### Debugging Full-Stack

```
1. Ctrl+Shift+D → "Backend + Web" → F5
2. Ambos servicios inician
3. Abre http://localhost:3000
4. Inspecciona llamadas a backend
5. Usa Chrome DevTools + VS Code Debug
```

## 🔗 Enlaces Útiles

- [VS Code Debugging Guide](https://code.visualstudio.com/docs/editor/debugging)
- [Python Debugging with debugpy](https://github.com/microsoft/debugpy)
- [Next.js Debugging](https://nextjs.org/docs/advanced-features/debugging)
- [Expo Debugging](https://docs.expo.dev/debugging/introduction/)

---

**¡Listo para debuggear!** 🎯 Usa `F5` para iniciar tu sesión de debug preferida.
