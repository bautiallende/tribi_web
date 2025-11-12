# 🚀 Inicio Rápido - Tribi eSIM

## ⚡ Empezar en 5 Minutos

### 1️⃣ Verificar MySQL está corriendo
```powershell
mysql -u root -p
# Ingresa tu password
```

### 2️⃣ Iniciar Backend
```powershell
cd apps\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
✅ Backend en: http://localhost:8000

### 3️⃣ Iniciar Web (Nueva terminal)
```powershell
cd apps\web
npm install
npm run dev
```
✅ Web en: http://localhost:3000

---

## 🎯 Rutas Principales

| Ruta | Descripción | Requiere Login |
|------|-------------|----------------|
| `/` | Home / Landing page | No |
| `/plans` | Catálogo de planes eSIM | No |
| `/auth` | Login con OTP por email | No |
| `/account` | Mi cuenta y pedidos | ✅ Sí |
| `/admin` | Panel de administración | ✅ Admin |
| `/admin/countries` | Gestionar países | ✅ Admin |
| `/admin/carriers` | Gestionar carriers | ✅ Admin |
| `/admin/plans` | Gestionar planes | ✅ Admin |

---

## 👤 Configurar Admin

1. Editar `apps/backend/.env`:
```bash
ADMIN_EMAILS=tu-email@ejemplo.com
```

2. Reiniciar backend (Ctrl+C y volver a ejecutar uvicorn)

3. Login en `/auth` con ese email

4. Ir a `/admin` ✅

---

## 🐛 Problemas Comunes

### "404 Page not found"
- ✅ Verifica que `npm run dev` esté corriendo en apps/web
- ✅ URL correcta: `/admin` (sin espacios)

### Login no funciona
- ✅ Backend debe estar corriendo en :8000
- ✅ Revisa logs del backend para ver el código OTP
- ✅ Sin MailHog, el código aparece en consola del backend

### No se ve texto en inputs (dark mode)
- ✅ Ya corregido en esta sesión
- ✅ Recargar la página (Ctrl+R)

### "Access Denied" en /admin
- ✅ Email debe estar en ADMIN_EMAILS
- ✅ Reiniciar backend después de cambiar .env
- ✅ Logout y login de nuevo

---

## 📖 Tutorial Completo

Ver **TUTORIAL.md** para:
- Guía paso a paso completa
- Uso de cada sección
- API endpoints
- Troubleshooting avanzado
- Tips de desarrollo

---

## 🎓 Flujo de Usuario Típico

### Como Usuario Regular:
1. Ir a `/plans`
2. Buscar plan deseado
3. Click "Buy Now"
4. Login en `/auth` (si es necesario)
5. Confirmar compra en checkout
6. Ver eSIM activado en `/account`

### Como Admin:
1. Login en `/auth` (con email en ADMIN_EMAILS)
2. Ir a `/admin`
3. Gestionar Countries, Carriers, Plans
4. Crear/Editar/Eliminar con modales
5. Buscar y filtrar contenido

---

## 🔗 Links Útiles

- **Web:** http://localhost:3000
- **Admin:** http://localhost:3000/admin
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **MailHog (si está corriendo):** http://localhost:8025

---

## ✅ Verificación Rápida

```powershell
# Backend health
curl http://localhost:8000/health
# Debe retornar: {"status":"healthy"}

# Web cargando
curl http://localhost:3000
# Debe retornar HTML

# Admin emails configurados
cd apps\backend
python -c "from app.core.config import settings; print(settings.admin_emails_list)"
# Debe mostrar tu email
```

---

## 🆘 Ayuda

Si nada funciona:

1. **Reiniciar todo:**
   ```powershell
   # Ctrl+C en ambas terminales
   # Cerrar y abrir nuevas terminales
   # Seguir pasos 2 y 3 de arriba
   ```

2. **Verificar puertos:**
   ```powershell
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000
   # Si hay procesos, matalos o usa otros puertos
   ```

3. **Reset database:**
   ```powershell
   mysql -u root -p
   DROP DATABASE tribi_dev;
   CREATE DATABASE tribi_dev;
   # Luego: alembic upgrade head
   ```

---

## 📚 Documentación Adicional

- `TUTORIAL.md` - Tutorial completo paso a paso
- `docs/ADMIN.md` - Guía del panel admin
- `docs/ARCHITECTURE.md` - Arquitectura del sistema
- `docs/TESTING.md` - Guía de testing

---

¡Listo para empezar! 🎉
