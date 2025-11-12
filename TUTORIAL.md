# 🚀 Tutorial: Cómo Usar Tribi eSIM Platform

## 📋 Tabla de Contenidos
1. [Inicio Rápido](#inicio-rápido)
2. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
3. [Configuración Inicial](#configuración-inicial)
4. [Usar la Aplicación Web](#usar-la-aplicación-web)
5. [Panel de Administración](#panel-de-administración)
6. [API Backend](#api-backend)
7. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 Inicio Rápido

### Prerrequisitos
- Python 3.10+ instalado
- Node.js 18+ instalado
- MySQL 8.0+ corriendo en localhost:3306
- Git instalado

### 1️⃣ Iniciar Base de Datos MySQL

**Opción A: MySQL local**
```powershell
# Verificar que MySQL esté corriendo
mysql -u root -p

# Crear base de datos
CREATE DATABASE tribi_dev;
```

**Opción B: Docker**
```powershell
cd infrastructure
docker-compose up -d mysql
```

### 2️⃣ Configurar Backend

```powershell
# Ir a la carpeta del backend
cd apps\backend

# Activar entorno virtual Python (si existe)
# Si no existe, crear uno:
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Verificar que .env existe con estos valores:
# MYSQL_HOST=localhost
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=1234
# MYSQL_DB=tribi_dev
# ADMIN_EMAILS=tu-email@ejemplo.com

# Ejecutar migraciones
alembic upgrade head

# (Opcional) Cargar datos de prueba
python -m app.seed.load_catalog
```

### 3️⃣ Iniciar Backend

```powershell
# Desde apps\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Deberías ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**✅ Backend corriendo en:** http://localhost:8000

### 4️⃣ Configurar Frontend (Web)

```powershell
# Abrir NUEVA terminal
cd apps\web

# Instalar dependencias (solo primera vez)
npm install

# Iniciar servidor de desarrollo
npm run dev
```

Deberías ver:
```
> web@0.1.0 dev
> next dev

  ▲ Next.js 14.x
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Ready in 2.5s
```

**✅ Web corriendo en:** http://localhost:3000

### 5️⃣ (Opcional) MailHog para Emails

Los códigos OTP se envían por email. En desarrollo, usa MailHog para capturarlos:

```powershell
# Instalar MailHog
# Windows: Descargar de https://github.com/mailhog/MailHog/releases
# O usar Docker:
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Ver emails en: http://localhost:8025
```

---

## 🏗️ Arquitectura del Proyecto

```
tribi_web/
├── apps/
│   ├── backend/          # FastAPI + SQLAlchemy
│   │   ├── app/
│   │   │   ├── api/      # Endpoints REST
│   │   │   │   ├── auth.py      # Login con OTP
│   │   │   │   ├── catalog.py   # Countries/Plans públicos
│   │   │   │   ├── orders.py    # Crear pedidos
│   │   │   │   └── admin.py     # CRUD admin
│   │   │   ├── models/   # SQLAlchemy models
│   │   │   ├── schemas/  # Pydantic schemas
│   │   │   └── core/     # Config, DB session
│   │   ├── alembic/      # Migraciones DB
│   │   └── tests/        # Tests pytest
│   │
│   ├── web/              # Next.js 14 (App Router)
│   │   ├── app/
│   │   │   ├── page.tsx           # Home
│   │   │   ├── auth/page.tsx      # Login
│   │   │   ├── plans/page.tsx     # Catálogo público
│   │   │   ├── account/page.tsx   # Cuenta usuario
│   │   │   └── admin/             # Panel admin
│   │   │       ├── layout.tsx     # Auth check
│   │   │       ├── page.tsx       # Dashboard
│   │   │       ├── countries/     # CRUD países
│   │   │       ├── carriers/      # CRUD carriers
│   │   │       └── plans/         # CRUD planes
│   │   └── components/   # Navbar, Footer, etc.
│   │
│   └── mobile/           # Expo/React Native
│       └── src/
│
├── docs/                 # Documentación
│   ├── ADMIN.md         # Guía del panel admin
│   ├── TESTING.md       # Guía de tests
│   └── ARCHITECTURE.md  # Arquitectura completa
│
└── infrastructure/       # Docker Compose
```

---

## ⚙️ Configuración Inicial

### Archivo .env del Backend

Ubicación: `apps/backend/.env`

```bash
# Base de datos MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=tribi_dev

# Puerto del backend
BACKEND_PORT=8000

# JWT Authentication
JWT_SECRET=dev-secret-key-change-in-prod
JWT_EXPIRES_MIN=1440  # 24 horas

# Email SMTP (MailHog en dev)
EMAIL_FROM=dev@tribi.local
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false

# CORS Origins
FRONTEND_ORIGINS=["http://localhost:3000","http://localhost:19006"]

# Admin Emails (comma-separated)
ADMIN_EMAILS=admin@tribi.app,tu-email@ejemplo.com

# Payment Provider
PAYMENT_PROVIDER=MOCK

# Rate Limiting
RATE_LIMIT_CODES_PER_MINUTE=1
RATE_LIMIT_CODES_PER_DAY=5
```

### Variables de Entorno del Frontend

Ubicación: `apps/web/.env.local` (crear si no existe)

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## 🌐 Usar la Aplicación Web

### 1. Página de Inicio (Home)

**URL:** http://localhost:3000

**Funcionalidad:**
- Hero section con CTA
- Características del servicio
- Link a "Browse Plans"

**Navegación:**
- Navbar superior: Home | Plans | Account | Admin (si eres admin)
- Footer con links

### 2. Ver Catálogo de Planes

**URL:** http://localhost:3000/plans

**Funcionalidad:**
- Lista de planes eSIM disponibles
- Filtros por país
- Botón "Buy Now" → redirige a checkout

**Ejemplo:**
```
📱 USA 10GB - AT&T
   10 GB data | 30 days
   $25.00
   [Buy Now]
```

### 3. Autenticación (Login)

**URL:** http://localhost:3000/auth

**Flujo:**

**Paso 1: Ingresar Email**
```
┌────────────────────────────┐
│ Email Address              │
│ [you@example.com        ]  │
│                            │
│ [Get OTP Code]             │
└────────────────────────────┘
```

1. Escribe tu email (ej: `test@tribi.app`)
2. Click "Get OTP Code"
3. El backend envía un código de 6 dígitos por email

**Paso 2: Ingresar Código OTP**
```
┌────────────────────────────┐
│ OTP sent to: test@tribi.app│
│                            │
│ Enter 6-digit Code         │
│ [ 1 2 3 4 5 6 ]           │
│                            │
│ [Back]  [Verify]           │
└────────────────────────────┘
```

1. Revisa tu email (o MailHog en http://localhost:8025)
2. Ingresa el código de 6 dígitos
3. Click "Verify"
4. Si es correcto → redirige a `/account`

**⚠️ En Desarrollo (sin MailHog):**
- Revisa la consola del backend
- Verás: `Your login code is: 123456`
- Copia ese código

### 4. Mi Cuenta

**URL:** http://localhost:3000/account (requiere login)

**Funcionalidad:**
- Ver información del usuario
- Lista de pedidos (orders)
- Estado de eSIMs activados

**Si no estás logueado:** Redirige a `/auth`

### 5. Checkout

**URL:** http://localhost:3000/checkout?planId=1

**Flujo:**
1. Selecciona un plan desde `/plans`
2. Click "Buy Now" → va a checkout
3. Revisa detalles del plan
4. Click "Confirm Purchase"
5. Pago simulado (MOCK provider)
6. eSIM activado automáticamente

---

## 👨‍💼 Panel de Administración

### Requisitos
Tu email debe estar en `ADMIN_EMAILS` del backend:

```bash
# apps/backend/.env
ADMIN_EMAILS=admin@tribi.app,tu-email@ejemplo.com
```

**⚠️ Importante:** Reinicia el backend después de cambiar esto.

### Acceso al Admin Panel

**URL:** http://localhost:3000/admin

**Flujo de Autenticación:**

1. **Ir a:** http://localhost:3000/admin
2. **Si NO estás logueado:**
   - Redirige a `/auth?redirect=/admin`
   - Haz login con tu email (debe estar en ADMIN_EMAILS)
   - Después del login → vuelve a `/admin`

3. **Si estás logueado pero NO eres admin:**
   - Muestra página "Access Denied"
   - Error 403: "Admin access required"
   - Botones: [Go Home] [Login]

4. **Si estás logueado Y eres admin:**
   - Muestra el Dashboard del Admin Panel ✅

### Dashboard Admin

```
┌─────────────────────────────────────────┐
│ Admin Panel          Back to Site →     │
├─────────────────────────────────────────┤
│ Dashboard                               │
│                                         │
│ ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│ │ 🌍       │  │ 📡       │  │ 📋       │ │
│ │Countries│  │Carriers │  │ Plans   │ │
│ │Manage → │  │Manage → │  │Manage → │ │
│ └─────────┘  └─────────┘  └─────────┘ │
│                                         │
│ Quick Info                              │
│ ✓ All actions support search/pagination│
│ ✓ Optimistic UI updates                │
│ ✓ Frontend & backend validation        │
└─────────────────────────────────────────┘
```

### Gestión de Countries

**URL:** http://localhost:3000/admin/countries

**Funcionalidades:**

1. **Ver Lista**
   - Tabla con ISO2 y Name
   - Paginación (20 items por página)

2. **Buscar**
   ```
   [Search by name or ISO2...              ]
   ```
   - Busca en tiempo real
   - Ej: "united" → encuentra "United States", "United Kingdom"

3. **Crear País**
   - Click "[+ Add Country]"
   - Modal aparece:
   ```
   ┌────────────────────────┐
   │ Add Country            │
   │                        │
   │ ISO2 Code              │
   │ [US]                   │
   │                        │
   │ Country Name           │
   │ [United States]        │
   │                        │
   │ [Cancel] [Create]      │
   └────────────────────────┘
   ```
   - ISO2: 2 letras (auto-uppercase)
   - Validación: duplicados rechazados

4. **Editar País**
   - Click "Edit" en cualquier fila
   - Modal pre-llenado con datos actuales
   - Modifica y click "[Update]"
   - **Optimistic Update:** UI actualiza inmediatamente

5. **Eliminar País**
   - Click "Delete" en cualquier fila
   - Modal de confirmación:
   ```
   ┌────────────────────────────────┐
   │ Delete Country                 │
   │                                │
   │ Are you sure you want to       │
   │ delete United States?          │
   │                                │
   │ [Cancel] [Delete]              │
   └────────────────────────────────┘
   ```
   - ⚠️ Falla si hay planes que referencian este país

6. **Toast Notifications**
   ```
   ┌─────────────────────┐
   │ ✓ Country created   │
   └─────────────────────┘
   ```
   - Auto-desaparece en 3 segundos
   - Verde = success, Rojo = error

### Gestión de Carriers

**URL:** http://localhost:3000/admin/carriers

Similar a Countries pero más simple:
- Solo tiene campo "Name"
- Buscar por nombre
- CRUD completo
- Previene eliminación si hay planes asociados

**Ejemplo de uso:**
```
1. Click [+ Add Carrier]
2. Nombre: "AT&T"
3. Click [Create]
4. ✓ Carrier created
```

### Gestión de Plans

**URL:** http://localhost:3000/admin/plans

**La más completa:**

**Filtros:**
```
[Search by name...] [All Countries ▼] [All Carriers ▼]
```
- Combina búsqueda + filtros
- Reset a página 1 al filtrar

**Tabla:**
```
Name         | Country | Carrier | Data   | Duration | Price   | Actions
──────────────────────────────────────────────────────────────────────────
USA 10GB     | USA     | AT&T    | 10 GB  | 30 days  | $25.00  | Edit Delete
Mexico 5GB   | Mexico  | Telcel  | 5 GB   | 7 days   | $15.00  | Edit Delete
```

**Crear Plan:**
```
┌─────────────────────────────────────┐
│ Add Plan                            │
│                                     │
│ Country *        Carrier *          │
│ [USA        ▼]  [AT&T       ▼]     │
│                                     │
│ Plan Name *                         │
│ [USA 10GB                        ]  │
│                                     │
│ Data (GB) *      Duration (days) *  │
│ [10.0       ]   [30            ]    │
│                                     │
│ Price (USD) *    ☐ Unlimited Data   │
│ [25.50      ]                       │
│                                     │
│ Description (optional)              │
│ [Best plan for travelers...      ]  │
│                                     │
│ [Cancel] [Create]                   │
└─────────────────────────────────────┘
```

**Validaciones:**
- ✅ Country y Carrier deben existir
- ✅ Price >= 0
- ✅ Duration > 0
- ✅ Data >= 0
- ❌ No hay validación de duplicados (se permite)

---

## 🔌 API Backend

### Endpoints Públicos

#### 1. Health Check
```http
GET http://localhost:8000/health
```
Respuesta:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### 2. Ver Países
```http
GET http://localhost:8000/api/countries?q=united
```
Respuesta:
```json
[
  {
    "id": 1,
    "iso2": "US",
    "name": "United States"
  }
]
```

#### 3. Ver Planes
```http
GET http://localhost:8000/api/plans?country=US&max_price=30
```
Respuesta:
```json
[
  {
    "id": 1,
    "name": "USA 10GB",
    "data_gb": 10.0,
    "duration_days": 30,
    "price_usd": 25.50,
    "country_id": 1,
    "carrier_id": 1
  }
]
```

### Endpoints de Autenticación

#### 4. Request OTP
```http
POST http://localhost:8000/auth/request-code
Content-Type: application/json

{
  "email": "test@tribi.app"
}
```
Respuesta:
```json
{
  "message": "code_sent"
}
```

#### 5. Verify OTP
```http
POST http://localhost:8000/auth/verify
Content-Type: application/json

{
  "email": "test@tribi.app",
  "code": "123456"
}
```
Respuesta:
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer"
}
```
**Cookie:** `tribi_token` (httpOnly)

#### 6. Get Current User
```http
GET http://localhost:8000/auth/me
Cookie: tribi_token=eyJ0eXAi...
```
Respuesta:
```json
{
  "id": 1,
  "email": "test@tribi.app",
  "name": null,
  "created_at": "2025-11-12T..."
}
```

### Endpoints Admin (requieren admin)

#### 7. List Countries (Admin)
```http
GET http://localhost:8000/admin/countries?page=1&page_size=20
Cookie: tribi_token=eyJ0eXAi...
```
Respuesta:
```json
{
  "items": [...],
  "total": 195,
  "page": 1,
  "page_size": 20,
  "total_pages": 10
}
```

#### 8. Create Country (Admin)
```http
POST http://localhost:8000/admin/countries
Content-Type: application/json
Cookie: tribi_token=eyJ0eXAi...

{
  "iso2": "US",
  "name": "United States"
}
```
Respuesta: `201 Created`

#### 9. Delete Country (Admin)
```http
DELETE http://localhost:8000/admin/countries/1
Cookie: tribi_token=eyJ0eXAi...
```
Respuesta: `204 No Content`

---

## 🐛 Solución de Problemas

### Problema 1: "404 This page could not be found"

**Síntomas:**
- Ir a `/admin` muestra error 404
- Rutas no funcionan

**Causas:**
1. ❌ Web server (Next.js) no está corriendo
2. ❌ Typo en la URL (ej: `/ admin` con espacio)

**Solución:**
```powershell
# Terminal 1: Backend
cd apps\backend
uvicorn app.main:app --reload

# Terminal 2: Web
cd apps\web
npm run dev

# Verificar:
# - Backend: http://localhost:8000/health
# - Web: http://localhost:3000
```

### Problema 2: No se ve el texto en inputs (dark mode)

**Síntomas:**
- Inputs blancos en dark mode
- No se ve lo que escribes

**Solución:**
✅ Ya corregido en esta sesión. Los inputs ahora tienen:
```tsx
className="... bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
```

### Problema 3: Login no funciona / "No pasa nada"

**Síntomas:**
- Click "Get OTP Code" → nada pasa
- No llega email
- Console muestra errores

**Diagnóstico:**
```powershell
# 1. Verificar backend corriendo
curl http://localhost:8000/health

# 2. Revisar logs del backend
# Deberías ver:
INFO:     POST /auth/request-code
INFO:     Sending email to test@tribi.app
```

**Causas comunes:**

**A) Backend no está corriendo**
```
Error: fetch failed
```
Solución: Inicia el backend (`uvicorn app.main:app --reload`)

**B) MySQL no está corriendo**
```
Error: Can't connect to MySQL server
```
Solución: Inicia MySQL

**C) Rate limit excedido**
```
Error: 429 Too Many Requests
```
Solución: Espera 60 segundos o cambia email

**D) Email no llega**
```
# Backend logs muestran:
Failed to send email: [Errno 111] Connection refused
```
Solución opciones:
1. Ignora (en dev): Revisa logs del backend para ver el código
2. Instala MailHog: `docker run -p 8025:8025 -p 1025:1025 mailhog/mailhog`

### Problema 4: "Access Denied" en Admin Panel

**Síntomas:**
- Login exitoso
- Ir a `/admin` → "Access Denied"

**Causa:**
Tu email no está en `ADMIN_EMAILS`

**Solución:**
```powershell
# 1. Editar apps\backend\.env
ADMIN_EMAILS=tu-email@ejemplo.com

# 2. Reiniciar backend
# Ctrl+C para detener
uvicorn app.main:app --reload

# 3. Logout y login de nuevo
# O espera 24h a que expire el token
```

**Verificar configuración:**
```powershell
cd apps\backend
python -c "from app.core.config import settings; print(settings.admin_emails_list)"
# Output: ['tu-email@ejemplo.com']
```

### Problema 5: CORS Errors en Console

**Síntomas:**
```
Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

**Solución:**
```bash
# apps\backend\.env
FRONTEND_ORIGINS=["http://localhost:3000"]
```

Reinicia backend.

### Problema 6: Database Errors

**Síntomas:**
```
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")
```

**Diagnóstico:**
```powershell
# Test MySQL connection
mysql -h localhost -P 3306 -u root -p
# Enter password: 1234
```

**Soluciones:**

**MySQL no instalado:**
```powershell
# Opción 1: Instalar MySQL
# Download: https://dev.mysql.com/downloads/mysql/

# Opción 2: Docker
docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=1234 mysql:8.0
```

**Password incorrecto:**
```bash
# apps\backend\.env
MYSQL_PASSWORD=tu-password-real
```

**Database no existe:**
```sql
-- En MySQL shell:
CREATE DATABASE tribi_dev;
```

### Problema 7: Migraciones Pendientes

**Síntomas:**
```
sqlalchemy.exc.OperationalError: (1146, "Table 'tribi_dev.users' doesn't exist")
```

**Solución:**
```powershell
cd apps\backend
alembic upgrade head

# Verificar:
alembic current
# Output: (head)
```

### Problema 8: Port Already in Use

**Síntomas:**
```
ERROR: [Errno 10048] Only one usage of each socket address is permitted
```

**Solución:**
```powershell
# Encontrar proceso usando puerto 8000
netstat -ano | findstr :8000

# Matar proceso
taskkill /PID <PID_NUMBER> /F

# O cambiar puerto:
uvicorn app.main:app --reload --port 8001
```

---

## 📚 Flujo Completo de Uso

### Escenario: Usuario Normal Compra un Plan

```
1. Usuario → http://localhost:3000
2. Click "Browse Plans" → /plans
3. Busca "USA" en filtros
4. Encuentra "USA 10GB - $25.00"
5. Click "Buy Now" → /checkout?planId=1
6. Si no está logueado → redirige a /auth
   a. Ingresa email: buyer@example.com
   b. Recibe OTP: 123456
   c. Verifica → redirige a /checkout
7. Confirma detalles del plan
8. Click "Confirm Purchase"
9. Payment MOCK → success
10. eSIM activado automáticamente
11. Redirige a /account
12. Ve su nuevo eSIM activo
```

### Escenario: Admin Gestiona Catálogo

```
1. Admin → http://localhost:3000/admin
2. Login con email en ADMIN_EMAILS
3. Dashboard → Click "Countries"
4. Click "+ Add Country"
5. Agrega: ISO2="BR", Name="Brazil"
6. Toast: "✓ Country created"
7. Back to Dashboard → Click "Carriers"
8. Click "+ Add Carrier"
9. Agrega: Name="Claro"
10. Dashboard → Click "Plans"
11. Click "+ Add Plan"
12. Completa formulario:
    - Country: Brazil
    - Carrier: Claro
    - Name: Brazil 15GB
    - Data: 15.0 GB
    - Duration: 30 days
    - Price: 35.00
13. Click "Create"
14. Toast: "✓ Plan created"
15. Plan aparece en /plans inmediatamente
```

---

## 🎓 Tips y Buenas Prácticas

### Durante Desarrollo

1. **Mantén 2 terminales abiertas:**
   - Terminal 1: Backend (uvicorn)
   - Terminal 2: Web (npm run dev)

2. **Usa MailHog para emails:**
   ```powershell
   docker run -d -p 8025:8025 -p 1025:1025 mailhog/mailhog
   ```
   Ver emails: http://localhost:8025

3. **Revisa logs del backend:**
   ```
   INFO:     POST /auth/request-code
   Your login code is: 123456
   ```

4. **Usa Postman/Thunder Client:**
   - Colección de endpoints disponible
   - Facilita testing de API

5. **Database Browser:**
   - Usa DBeaver, MySQL Workbench, o TablePlus
   - Conecta a localhost:3306
   - Revisa tablas: users, auth_codes, orders, etc.

### Testing

```powershell
# Backend tests
cd apps\backend
pytest tests/ -v

# Test específico
pytest tests/test_admin_auth.py -v

# Con coverage
pytest --cov=app tests/
```

### Seed Data

```powershell
cd apps\backend
python -m app.seed.load_catalog

# Carga:
# - 195 países
# - 10 carriers
# - 50 planes de ejemplo
```

---

## 📞 Recursos Adicionales

- **Documentación Completa:** `docs/ADMIN.md`
- **Testing Guide:** `docs/TESTING.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **API Examples:** `docs/API_EXAMPLES.md`

- **Backend API Docs:** http://localhost:8000/docs (Swagger UI)
- **ReDoc:** http://localhost:8000/redoc

---

## ✅ Checklist de Verificación

Antes de reportar un problema, verifica:

```
Backend:
□ MySQL está corriendo
□ Database 'tribi_dev' existe
□ Migraciones aplicadas (alembic upgrade head)
□ Backend corriendo en :8000
□ /health retorna {"status": "healthy"}

Frontend:
□ npm install completado sin errores
□ npm run dev corriendo en :3000
□ http://localhost:3000 carga correctamente

Admin:
□ Email en ADMIN_EMAILS del .env
□ Backend reiniciado después de cambiar .env
□ Login exitoso con email admin
□ /admin/countries carga sin errores

General:
□ No hay otros procesos usando puertos 8000/3000
□ Firewall permite conexiones localhost
□ Navegador tiene cookies habilitadas
```

---

## 🎉 Próximos Pasos

Después de dominar lo básico:

1. **Explora la API:** http://localhost:8000/docs
2. **Crea planes de prueba:** Usa el admin panel
3. **Simula compras:** Como usuario regular
4. **Revisa el código:** Empieza por `apps/backend/app/api/`
5. **Modifica y experimenta:** Hot reload en ambos lados

¡Disfruta construyendo con Tribi! 🚀
