# Autostock - Sistema SaaS para Montallantas

Sistema de gestión de inventario y ventas tipo SaaS diseñado específicamente para negocios de montallantas. Construido con Python FastAPI, SQLite y frontend puro (HTML5, CSS3, JavaScript).

## 🚀 Características

- **Tres niveles de acceso**: SuperAdministrador, Administrador de Montallantas y Vendedor
- **Interfaz responsive**: Optimizada para uso móvil (mobile-first)
- **Gestión completa**: Inventario, ventas, usuarios, reportes y backups
- **Arquitectura SaaS**: Multi-negocio con suscripciones
- **Tecnología moderna**: FastAPI + SQLAlchemy + SQLite

## 🏗️ Arquitectura

```
/app/
├── main.py                 # Punto de entrada FastAPI
├── routers/                # Endpoints por rol
│   ├── auth.py            # Autenticación
│   ├── superadmin.py      # SuperAdministrador
│   ├── admin_negocio.py   # Administrador
│   └── vendedor.py        # Vendedor
├── models/                # Modelos de datos SQLAlchemy
│   ├── user.py
│   ├── negocio.py
│   ├── producto.py
│   ├── venta.py
│   └── plan.py
├── templates/             # Templates HTML Jinja2
├── static/                # Archivos estáticos
│   ├── css/styles.css
│   └── js/
└── database/             # Base de datos SQLite
    └── inventario.db
```

## 📋 Requisitos del Sistema

- Python 3.8+
- Sistema operativo: Linux (Debian 10+), Windows 10+, macOS
- Navegador web moderno con soporte JavaScript

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/autostock.git
cd autostock
```

### 2. Crear entorno virtual

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Inicializar base de datos

```bash
cd app
python init_db.py
```

Esto creará:
- La base de datos SQLite (`database/inventario.db`)
- Usuario superadmin: `superadmin` / `admin123`
- Tres planes de suscripción básicos

### 5. Ejecutar la aplicación

```bash
# Desde el directorio app/
python main.py

# O desde la raíz del proyecto
python -m app.main
```

La aplicación estará disponible en: http://localhost:8000

## 👥 Roles y Funcionalidades

### 🔐 SuperAdministrador del Sistema
**Usuario inicial**: `superadmin` / `admin123`

**Funciones**:
- Gestionar negocios clientes
- Configurar planes de suscripción
- Visualizar métricas globales
- Generar backups de datos
- Restablecer contraseñas

**URLs principales**:
- `/superadmin/dashboard`
- `/superadmin/negocios`
- `/superadmin/planes`
- `/superadmin/backups`

### 🏪 Administrador de Montallantas

**Funciones**:
- CRUD completo de productos
- Registro y seguimiento de ventas
- Gestión de empleados (vendedores)
- Visualización de reportes
- Exportación de datos

**URLs principales**:
- `/negocio/dashboard`
- `/negocio/inventario`
- `/negocio/ventas`
- `/negocio/usuarios`
- `/negocio/reportes`

### 👤 Vendedor

**Funciones**:
- Consultar inventario de productos
- Registrar ventas
- Ver historial personal
- Escanear productos (simulado)

**URLs principales**:
- `/vendedor/dashboard`
- `/vendedor/inventario`
- `/vendedor/ventas`
- `/vendedor/ventas/historial`

## 🎨 Diseño y UX

### Paleta de Colores
- **Azul oscuro** (#1A2238): Headers, navegación principal
- **Gris medio** (#E0E3E7): Fondos secundarios, separadores
- **Verde menta** (#3AB795): Éxito, SuperAdministrador
- **Naranja suave** (#F6AE2D): Advertencias, Administrador
- **Blanco** (#FFFFFF): Fondos principales

### Diseño Responsive
- Mobile-first approach
- Optimizado para celulares y tablets
- Navegación horizontal en desktop
- Componentes adaptables

## 🗄️ Base de Datos

### Tablas Principales

```sql
-- Usuarios del sistema
usuarios (
    id, nombre_usuario, contraseña, rol,
    negocio_id, estado, fecha_creacion
)

-- Negocios clientes
negocios (
    id, nombre_negocio, propietario, fecha_registro,
    plan_id, estado_suscripcion, fecha_vencimiento
)

-- Planes de suscripción
planes (id, nombre_plan, descripcion, precio, duracion_dias)

-- Productos por negocio
productos (
    id, negocio_id, nombre, codigo, categoria,
    precio, cantidad, proveedor, fecha_registro
)

-- Ventas registradas
ventas (
    id, negocio_id, producto_id, vendedor_id,
    cantidad_vendida, valor_total, fecha_venta
)
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` en la raíz:

```env
DATABASE_URL=sqlite:///./database/inventario.db
SECRET_KEY=tu_clave_secreta_muy_segura_aqui
ACCESS_TOKEN_EXPIRE_MINUTES=30
DEBUG=True
```

### Configuración de Backups

Los backups se generan automáticamente en formato CSV:
- `/superadmin/backups/download/usuarios`
- `/superadmin/backups/download/negocios`
- `/superadmin/backups/download/productos`
- `/superadmin/backups/download/ventas`

## 📊 API REST

### Endpoints principales

```
GET  /health                    # Health check
POST /login                     # Autenticación
GET  /dashboard                 # Dashboard por rol

# SuperAdmin
GET  /superadmin/dashboard
GET  /superadmin/negocios
POST /superadmin/planes

# Admin
GET  /negocio/dashboard
GET  /negocio/inventario
POST /negocio/ventas

# Vendedor
GET  /vendedor/dashboard
GET  /vendedor/inventario
POST /vendedor/ventas
```

## 🚀 Despliegue en Producción

### 1. Configuración del servidor

```bash
# Instalar uvicorn con workers
pip install uvicorn[standard]

# Ejecutar con múltiples workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Base de datos PostgreSQL (opcional)

Para producción, cambiar a PostgreSQL:

```python
# En models/__init__.py
DATABASE_URL = "postgresql://user:password@localhost/autostock"
```

### 3. Configuración Nginx

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. SSL con Let's Encrypt

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Generar certificado
sudo certbot --nginx -d tu-dominio.com
```

## 🔒 Seguridad

- **Autenticación JWT** con expiración de tokens
- **Hash de contraseñas** con bcrypt
- **Validación de entrada** en frontend y backend
- **Protección CSRF** en formularios
- **Headers de seguridad** configurados

## 🐛 Solución de Problemas

### Error de base de datos
```bash
# Reinicializar base de datos
cd app
rm database/inventario.db
python init_db.py
```

### Problemas de dependencias
```bash
# Reinstalar en entorno virtual limpio
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Puerto ocupado
```bash
# Cambiar puerto
uvicorn app.main:app --port 8001
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📞 Soporte

Para soporte técnico:
- Crear issue en GitHub
- Email: soporte@autostock.com
- Documentación: https://docs.autostock.com

---

**Desarrollado con ❤️ para el sector de montallantas**
