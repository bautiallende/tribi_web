# Debug y Rutas - Tribi eSIM Platform

## ✅ PROBLEMAS SOLUCIONADOS

### 1. **App Móvil - Error de Actualización Remota**
**Error**: `java.io.IOException: Failed to download remote update`

**Causa**: Expo intentaba descargar actualizaciones OTA en modo desarrollo

**Solución**:
- Deshabilitado completamente el sistema de actualizaciones en `apps/mobile/app.config.js`
- Cambiado `runtimeVersion` a usar `nativeVersion`

```javascript
updates: {
  enabled: false
},
runtimeVersion: {
  policy: "nativeVersion"
}
```

### 2. **Frontend Admin - 404 Not Found**
**Error**: Página `/admin` devuelve 404

**Estado**: Las páginas admin existen en:
- `/apps/web/app/admin/page.tsx` ✅
- `/apps/web/app/admin/countries/page.tsx` ✅
- `/apps/web/app/admin/carriers/page.tsx` ✅
- `/apps/web/app/admin/plans/page.tsx` ✅

**Nota**: Necesitas reiniciar el servidor Next.js para que reconozca las nuevas páginas.

### 3. **Auth - Login no funciona**
**Error**: Rutas de autenticación devolvían 404

**Causa**: Faltaba el prefijo `/api` en las rutas del frontend

**Solución**: Actualizado `apps/web/app/auth/page.tsx`:
- `/auth/request-code` → `/api/auth/request-code` ✅
- `/auth/verify` → `/api/auth/verify` ✅

## 📋 MAPA DE RUTAS BACKEND (FastAPI)

### Rutas Públicas
```
GET  /health                     → Health check
GET  /api/catalog/countries      → Lista de países disponibles
GET  /api/catalog/plans          → Lista de planes disponibles
```

### Rutas de Autenticación
```
POST /api/auth/request-code      → Solicitar código OTP
POST /api/auth/verify            → Verificar código y obtener JWT
GET  /api/auth/me                → Obtener usuario actual (requiere auth)
```

### Rutas de Órdenes (Requieren Autenticación)
```
POST /api/orders                 → Crear orden
GET  /api/orders                 → Listar órdenes del usuario
GET  /api/orders/{id}            → Detalle de orden
```

### Rutas de Pagos (Requieren Autenticación)
```
POST /api/payments/create-intent → Crear intención de pago (Stripe)
POST /api/payments/confirm       → Confirmar pago
```

### Rutas de eSIMs (Requieren Autenticación)
```
GET  /api/esims                  → Listar eSIMs del usuario
POST /api/esims/{id}/activate    → Activar eSIM
```

### Rutas de Admin (Requieren Auth + Admin Role)
```
# Countries
GET    /admin/countries          → Listar países (paginado, búsqueda, ordenamiento)
POST   /admin/countries          → Crear país
PUT    /admin/countries/{id}     → Actualizar país
DELETE /admin/countries/{id}     → Eliminar país

# Carriers
GET    /admin/carriers           → Listar carriers (paginado, búsqueda, ordenamiento)
POST   /admin/carriers           → Crear carrier
PUT    /admin/carriers/{id}      → Actualizar carrier
DELETE /admin/carriers/{id}      → Eliminar carrier

# Plans
GET    /admin/plans              → Listar planes (paginado, búsqueda, filtros, ordenamiento)
POST   /admin/plans              → Crear plan
PUT    /admin/plans/{id}         → Actualizar plan
DELETE /admin/plans/{id}         → Eliminar plan
GET    /admin/plans/export       → Exportar planes a CSV
POST   /admin/plans/import       → Importar planes desde CSV
```

## 📋 MAPA DE RUTAS FRONTEND (Next.js)

### Páginas Públicas
```
/                                → Landing page
/plans                           → Catálogo de planes
/health                          → Health check page
```

### Páginas de Autenticación
```
/auth                            → Login con OTP (email → código)
```

### Páginas de Usuario (Requieren Auth)
```
/account                         → Dashboard del usuario
/checkout                        → Proceso de compra
```

### Páginas de Admin (Requieren Auth + Admin Role)
```
/admin                           → Dashboard admin
/admin/countries                 → Gestión de países
/admin/carriers                  → Gestión de carriers
/admin/plans                     → Gestión de planes
```

## 🔧 LOGS EN DESARROLLO

### Backend (FastAPI)
Se agregó middleware de logging que registra:
- ➡️ Cada request entrante (método, path, query params)
- ⬅️ Cada response saliente (status code, tiempo de procesamiento)

**Ejemplo de logs**:
```
➡️  POST /api/auth/request-code
   Query params: {}
⬅️  POST /api/auth/request-code - Status: 200 - Time: 0.123s
```

### Frontend Web (Next.js)
Se agregaron console.log en:
- `apps/web/app/auth/page.tsx` - Login flow
  - 🔑 Requesting OTP
  - 🔐 Verifying code
  - ✅ Success / ❌ Error

### App Móvil (React Native)
Se agregaron console.log en:
- `apps/mobile/src/api/client.ts` - API client
  - 📡 API Request (método, endpoint, body)
  - 📥 API Response (status code)
  - ✅ API Success / ❌ API Error

## 🚀 CÓMO PROBAR

### 1. Inicia el Backend
```bash
cd apps/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Verifica logs**: Deberías ver requests y responses en la consola

### 2. Inicia el Frontend Web
```bash
cd apps/web
npm run dev
```

**Navega a**:
- http://localhost:3000 - Landing page
- http://localhost:3000/auth - Login
- http://localhost:3000/admin - Admin panel (requiere auth)

**Verifica logs**: Abre DevTools (F12) y ve la consola

### 3. Inicia la App Móvil
```bash
cd apps/mobile
npm run start
```

**Escanea QR** con Expo Go

**Verifica logs**: Los logs aparecerán en:
- Terminal donde ejecutaste `npm run start`
- Expo DevTools en el navegador
- Dentro de la app (agita el dispositivo → Debug JS Remotely)

## 🐛 TROUBLESHOOTING

### Backend no responde
1. Verifica que está corriendo: http://localhost:8000/health
2. Revisa logs en la terminal del backend
3. Verifica que el puerto 8000 no esté ocupado

### Frontend 404 en /admin
1. Reinicia el servidor Next.js (Ctrl+C y `npm run dev`)
2. Verifica que existan los archivos en `apps/web/app/admin/`
3. Limpia cache: `rm -rf .next` y reinicia

### App móvil no conecta
1. Verifica la IP en `app.config.js` (debe ser tu IP local, no localhost)
2. Verifica que backend y móvil estén en la misma red
3. Verifica firewall no bloquee puerto 8000

### Error de autenticación
1. Verifica que SMTP esté configurado en `.env` (o usa modo dev)
2. En modo dev, cualquier código funciona (000000)
3. Revisa logs del backend para ver el código generado

## 📊 VARIABLES DE ENTORNO

### Backend (.env)
```bash
# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/tribi

# SMTP (opcional en dev)
SMTP_USER=your@email.com
SMTP_PASSWORD=your-password
SMTP_FROM=noreply@tribi.com

# Admin
ADMIN_EMAILS=admin@tribi.com,manager@tribi.com

# JWT
JWT_SECRET=your-secret-key-change-in-production

# Frontend
FRONTEND_ORIGINS=http://localhost:3000,http://192.168.1.102:19000
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

### Mobile (app.config.js)
```javascript
extra: {
  apiBase: "http://192.168.1.102:8000"  // Tu IP local
}
```

## ✅ CHECKLIST DE VERIFICACIÓN

- [ ] Backend corriendo en puerto 8000
- [ ] Frontend corriendo en puerto 3000  
- [ ] App móvil conectada vía Expo Go
- [ ] Logs visibles en backend (requests/responses)
- [ ] Logs visibles en frontend (DevTools console)
- [ ] Logs visibles en móvil (terminal/Expo DevTools)
- [ ] `/health` responde 200
- [ ] `/auth` permite login
- [ ] `/admin` muestra panel (después de auth)
- [ ] App móvil puede hacer login

## 🎯 PRÓXIMOS PASOS

1. **Probar autenticación completa**:
   - Frontend: Ir a /auth, ingresar email, verificar código
   - Móvil: Abrir app, ingresar email, verificar código

2. **Probar admin panel**:
   - Login con email en ADMIN_EMAILS
   - Navegar a /admin
   - Probar search, sorting, pagination
   - Probar CRUD operations
   - Probar CSV import/export

3. **Verificar logs en cada paso**:
   - Backend debe mostrar cada request
   - Frontend debe mostrar cada acción
   - Móvil debe mostrar cada API call

## 📝 NOTAS IMPORTANTES

- **Modo Desarrollo**: Los logs son verbosos intencionalmente
- **Modo Producción**: Deberás reducir el nivel de logs
- **SMTP**: En desarrollo, el código se imprime en logs del backend
- **Admin**: Solo emails en ADMIN_EMAILS pueden acceder a /admin
- **CORS**: Backend acepta requests de localhost:3000 y tu IP local
