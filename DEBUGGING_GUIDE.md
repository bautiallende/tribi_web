# 🔍 Guía de Debugging y Testing - Tribi

## 🚨 Problemas Resueltos

### ❌ Error: Admin 404 "This page could not be found"
**Causa:** El `admin/layout.tsx` estaba llamando a `/auth/me` sin el prefijo `/api`

**Solución:** Cambiado a `/api/auth/me` en línea 19 de `apps/web/app/admin/layout.tsx`

**Verificación:** 
```bash
# En la consola del navegador deberías ver:
🔐 Admin layout: Checking authentication...
📥 Admin auth response: 200
✅ User authenticated: admin@example.com
🔍 Checking admin privileges...
📥 Admin check response: 200
✅ Admin access confirmed
```

### ❌ Error: Mobile OTA "Failed to download remote updates"
**Causa:** Expo intentaba buscar actualizaciones OTA aunque no las usamos en desarrollo

**Solución:** Actualizado `apps/mobile/app.config.js` con:
- `updates.enabled: false`
- `updates.checkAutomatically: "OFF"`
- `updates.url: undefined`
- `eas.projectId: undefined`

**Verificación:** El error debería desaparecer después de reiniciar con cache limpio:
```powershell
cd apps/mobile
npx expo start --clear
```

## 📊 Logs del Sistema

### Backend (FastAPI)
Los logs del backend muestran todas las peticiones con este formato:
```
➡️  GET /api/auth/me
⬅️  GET /api/auth/me - Status: 200 - Time: 0.008s
```

**Qué buscar:**
- ✅ **Correcto:** `➡️  GET /api/auth/me` (con `/api`)
- ❌ **Error:** `➡️  GET /auth/me` (sin `/api`) → Indica que el frontend no está usando el prefijo correcto

### Frontend Web (Next.js)
Los logs en la consola del navegador usan emojis para identificar cada flujo:

**Auth Flow:**
```
🔑 Requesting OTP for: user@example.com
📥 Response status: 200
✅ OTP sent successfully
🔐 Verifying code for: user@example.com
✅ Login successful
```

**User Account:**
```
👤 Fetching user profile...
📥 Profile response: 200
✅ User profile loaded
📦 Fetching orders...
✅ Orders loaded: 0 orders
```

**Admin Access:**
```
🔐 Admin layout: Checking authentication...
📥 Admin auth response: 200
✅ User authenticated: admin@example.com
🔍 Checking admin privileges...
✅ Admin access confirmed
```

**Checkout Flow:**
```
🛒 Creating order for plan: 123
💳 Processing payment...
📱 Activating eSIM...
✅ eSIM activated successfully
```

### Mobile App (React Native + Expo)
Los logs en Metro bundler/terminal muestran:
```
📡 API Request: GET /api/auth/me
   Full URL: http://192.168.1.102:8000/api/auth/me
📥 API Response: 200 OK
✅ API Success: { email: "user@example.com" }
```

**Errores:**
```
❌ API Error: { detail: "Not authenticated" }
```

## 🧪 Script de Pruebas Completo

Creé un script Python que verifica todos los endpoints: `test_api_complete.py`

### Uso:
```powershell
# Asegúrate de que el backend esté corriendo en puerto 8000
cd apps\backend
python ..\..\test_api_complete.py
```

### Qué prueba:
1. ✅ Health check
2. ✅ Get countries (público)
3. ✅ Request OTP
4. ✅ Verify OTP (requiere ingresar el código de los logs)
5. ✅ Get current user (`/api/auth/me`)
6. ✅ Get user orders (`/api/orders/mine`)
7. ✅ Admin access (si el usuario es admin)
8. ✅ Logout

### Salida esperada:
```
🧪 TRIBI API TEST SUITE
Testing API at: http://localhost:8000

============================================================
               BASIC TESTS (No Auth Required)
============================================================

▶ Health check ... ✓ PASS (status=ok)
▶ Get countries list ... ✓ PASS (25 countries)

============================================================
                  USER AUTHENTICATION FLOW
============================================================

▶ Request OTP for test@example.com ... ✓ PASS (OTP sent)
▶ Waiting for OTP input ... 
Enter OTP code: 123456
✓ PASS (OTP entered: 123456)
▶ Verify OTP for test@example.com ... ✓ PASS (Authenticated)

============================================================
               AUTHENTICATED USER TESTS
============================================================

▶ Get current user ... ✓ PASS (email=test@example.com)
▶ Get user orders ... ✓ PASS (0 orders)

============================================================
            ADMIN TESTS (May fail if not admin)
============================================================

▶ Admin: Get countries (with pagination) ... ✓ PASS (25 total countries)

============================================================
TEST SUMMARY
============================================================
Total tests: 8
Passed: 8
Failed: 0

✓ ALL TESTS PASSED!
```

## 🔧 Checklist de Debugging Rápido

### 1. Backend no arranca
```powershell
cd apps\backend
# Verificar que el .env existe y tiene las variables necesarias
type .env

# Verificar que MySQL está corriendo
docker ps

# Intentar arrancar
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend muestra 404 en rutas /api/*
**Problema:** El fetch no está usando el prefijo `/api`

**Dónde buscar:**
```typescript
// ❌ INCORRECTO
fetch(`${API_BASE}/auth/me`)

// ✅ CORRECTO
fetch(`${API_BASE}/api/auth/me`)
```

**Archivos a revisar:**
- `apps/web/app/auth/page.tsx`
- `apps/web/app/account/page.tsx`
- `apps/web/app/checkout/page.tsx`
- `apps/web/app/plans/[iso2]/page.tsx`
- `apps/web/app/admin/layout.tsx` ⚠️ **Este era el problema**

### 3. Admin dice "Access Denied"
**Verificar que el email está en ADMIN_EMAILS:**
```powershell
cd apps\backend
type .env | findstr ADMIN_EMAILS
```

**Formato correcto:**
```env
ADMIN_EMAILS=admin@example.com,otro@example.com
```

### 4. Mobile app no se conecta al backend
**Verificar la IP en app.config.js:**
```javascript
extra: {
  apiBase: "http://192.168.1.102:8000"  // Debe ser tu IP local, NO localhost
}
```

**Encontrar tu IP:**
```powershell
ipconfig | findstr IPv4
```

### 5. Cookies no se guardan
**Verificar en backend que CORS permite credentials:**
```python
# En app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,  # ✅ DEBE estar en True
    allow_origins=["http://localhost:3000"],
)
```

**Verificar en frontend que fetch usa credentials:**
```typescript
fetch(url, {
  credentials: "include"  // ✅ DEBE estar presente
})
```

## 📝 Patrón de Rutas Correctas

### Backend (FastAPI)
```
/health                          → Health check (público)
/api/auth/request-code          → Solicitar OTP (público)
/api/auth/verify                → Verificar OTP (público)
/api/auth/me                    → Usuario actual (autenticado)
/api/auth/logout                → Cerrar sesión (autenticado)
/api/orders                     → Crear orden (autenticado)
/api/orders/mine                → Mis órdenes (autenticado)
/api/payments/create            → Crear pago (autenticado)
/api/esims/activate             → Activar eSIM (autenticado)
/api/countries                  → Listar países (público)
/admin/countries                → CRUD países (admin)
/admin/carriers                 → CRUD carriers (admin)
/admin/plans                    → CRUD plans (admin)
```

### Frontend (Next.js)
```
/                               → Home
/auth                           → Login con OTP
/auth/login?redirect=/admin     → Login con redirect
/account                        → Dashboard usuario
/plans/:country                 → Planes por país
/checkout                       → Checkout y pago
/admin                          → Dashboard admin
/admin/countries                → Gestión países
/admin/carriers                 → Gestión carriers
/admin/plans                    → Gestión planes
```

## 🎯 Próximos Pasos para Testing

1. **Reiniciar el frontend web** para que tome los cambios:
   ```powershell
   # Detener con Ctrl+C y reiniciar
   cd apps\web
   npm run dev
   ```

2. **Reiniciar la app móvil** con cache limpio:
   ```powershell
   cd apps\mobile
   npx expo start --clear
   ```

3. **Probar el flujo completo:**
   - Login como usuario regular → Ver account
   - Login como admin → Ver admin panel
   - Crear una orden → Ver en /account
   - Ejecutar `test_api_complete.py`

4. **Verificar logs en cada paso:**
   - Backend: Buscar `➡️` y `⬅️`
   - Frontend: Buscar emojis 🔑🔐👤📦💳📱
   - Mobile: Buscar 📡📥✅❌

## 🐛 Cómo Reportar un Bug

Cuando encuentres un problema, incluye:

1. **Logs del backend** (con los timestamps):
   ```
   2025-11-17 17:52:45,289 - app.main - INFO - ➡️  GET /api/auth/me
   2025-11-17 17:52:45,289 - app.main - INFO - ⬅️  GET /api/auth/me - Status: 404
   ```

2. **Logs de la consola del navegador**:
   ```
   🔐 Admin layout: Checking authentication...
   ❌ Not authenticated, redirecting to login
   ```

3. **URL que estabas intentando acceder**:
   ```
   http://localhost:3000/admin
   ```

4. **Email que usaste** (si es relevante):
   ```
   admin@example.com
   ```

5. **Código de respuesta HTTP**:
   ```
   404 Not Found
   ```

Con esta información puedo identificar rápidamente dónde está el problema.

## ✅ Verificación Final

Ejecuta este checklist después de cualquier cambio:

- [ ] Backend arranca sin errores
- [ ] Health check responde 200: `curl http://localhost:8000/health`
- [ ] Frontend arranca sin errores
- [ ] Login funciona (ver logs con 🔑✅)
- [ ] Account page carga (ver logs con 👤📦)
- [ ] Admin access funciona si eres admin (ver logs con 🔐✅)
- [ ] Mobile app arranca sin error de OTA
- [ ] Script `test_api_complete.py` pasa todos los tests

## 🔗 Documentación Relacionada

- [DEBUG_ROUTES.md](./DEBUG_ROUTES.md) - Mapa completo de rutas
- [ADMIN.md](./docs/ADMIN.md) - Documentación del panel admin
- [TESTING.md](./docs/TESTING.md) - Guía de testing general
- [QUICKSTART.md](./QUICKSTART.md) - Guía de inicio rápido
