# MySQL Setup Guide

## Configuración Local de MySQL

Esta guía te ayudará a configurar MySQL para desarrollo local.

### Requisitos Previos

1. **MySQL Server** instalado y ejecutándose
   - Versión: 5.7+
   - Puerto: 3306 (default)

2. **Credenciales**
   ```
   Usuario: root
   Contraseña: 1234
   Host: localhost:3306
   ```

3. **Python Virtual Environment** activado
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

### Instalación (Primera vez)

#### Paso 1: Verificar MySQL está corriendo

```powershell
# En Windows, verifica que el servicio MySQL está ejecutándose
# O desde terminal:
mysql -h localhost -u root -p1234 -e "SELECT 1;"
```

#### Paso 2: Crear la base de datos y tablas

```powershell
cd apps/backend
python setup_mysql.py
```

Esto hará:
- ✅ Crear la base de datos `tribi_dev`
- ✅ Crear todas las tablas (users, auth_codes, orders, payments, etc.)
- ✅ Verificar la conexión

### Archivo de Configuración (.env)

El archivo `.env` en `apps/backend/.env` contiene:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=tribi_dev
```

**⚠️ Nota:** Este archivo está configurado para dev local. En producción usa variables de entorno seguros.

### Uso Diario

#### 1. Conectar y verificar datos

```powershell
# Conectar a MySQL
mysql -h localhost -u root -p1234 -D tribi_dev

# Ver tablas
SHOW TABLES;

# Ver estructura de una tabla
DESCRIBE users;

# Ver datos
SELECT * FROM users;
```

#### 2. Ejecutar pruebas con MySQL

```powershell
cd apps/backend
python -m pytest tests/ -v
```

Los tests ahora usarán MySQL en lugar de SQLite.

#### 3. Ejecutar migraciones Alembic

```powershell
cd apps/backend
alembic upgrade head
```

#### 4. Iniciar el servidor backend

```powershell
cd apps/backend
python -m uvicorn app.main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

### Comandos Útiles

#### Resetear la base de datos

```powershell
# Opción 1: Eliminar y recrear (destructivo)
mysql -h localhost -u root -p1234 -e "DROP DATABASE tribi_dev;"
python setup_mysql.py

# Opción 2: Borrar tablas y recrear
mysql -h localhost -u root -p1234 -D tribi_dev -e "
  DROP TABLE IF EXISTS payments;
  DROP TABLE IF EXISTS esim_profiles;
  DROP TABLE IF EXISTS orders;
  DROP TABLE IF EXISTS auth_codes;
  DROP TABLE IF EXISTS users;
  DROP TABLE IF EXISTS plans;
  DROP TABLE IF EXISTS carriers;
  DROP TABLE IF EXISTS countries;
"
python setup_mysql.py
```

#### Ver logs de conexión

```powershell
# En el archivo .env, cambia la URL si necesitas más verbosidad
# Luego en Python:
from sqlalchemy import create_engine
engine = create_engine(database_url, echo=True)
```

#### Insertar datos de prueba

```sql
-- Conectarse a la DB
mysql -h localhost -u root -p1234 -D tribi_dev

-- Insertar país
INSERT INTO countries (iso2, name) VALUES ('US', 'United States');

-- Insertar carrier
INSERT INTO carriers (name) VALUES ('Verizon');

-- Insertar plan
INSERT INTO plans (country_id, carrier_id, name, data_gb, duration_days, price_usd)
VALUES (1, 1, 'US 5GB 30D', 5.00, 30, 19.99);

-- Ver datos
SELECT * FROM plans;
```

### Troubleshooting

#### ❌ "Access denied for user 'root'@'localhost'"

Verifica las credenciales en `.env`:
```env
MYSQL_USER=root
MYSQL_PASSWORD=1234
```

#### ❌ "Can't connect to MySQL server on 'localhost:3306'"

MySQL no está corriendo. Inicia el servicio:

**Windows:**
```powershell
# Usar Services (services.msc) o
net start MySQL80  # o el nombre de tu servicio MySQL
```

**macOS:**
```bash
brew services start mysql
```

**Linux:**
```bash
sudo systemctl start mysql
```

#### ❌ "Table 'tribi_dev.users' doesn't exist"

Ejecuta el setup nuevamente:
```powershell
python setup_mysql.py
```

### Variables de Entorno Adicionales

Ver `app/core/config.py` para todas las opciones:

```env
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DB=tribi_dev

# Backend
BACKEND_PORT=8000
BACKEND_CORS_ORIGINS=["http://localhost:3000"]

# Auth
JWT_SECRET=dev-secret-key-change-in-prod
JWT_EXPIRES_MIN=60

# Email
EMAIL_FROM=dev@tribi.local
SMTP_HOST=localhost
SMTP_PORT=1025

# Payments
PAYMENT_PROVIDER=MOCK
```

---

**Próximas pasos:**
1. ✅ Base de datos MySQL creada
2. ⏳ Ejecutar tests: `pytest tests/ -v`
3. ⏳ Iniciar servidor: `python -m uvicorn app.main:app --reload`
4. ⏳ Crear páginas web con los endpoints
