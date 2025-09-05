# 🏆 Bracket - Sistema de Gestión de Torneos (Edición Hispanohablante)

<div align="center">
  
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

**Sistema profesional de gestión de torneos con árbitros y scheduling avanzado**

[Documentación](./backend/API_DOCUMENTATION_ES.md) • [API Demo](http://localhost:8000/docs) • [Reportar Bug](https://github.com/evroon/bracket/issues)

</div>

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Nuevas Funcionalidades](#-nuevas-funcionalidades-edición-hispanohablante)
- [Arquitectura](#-arquitectura)
- [Instalación](#-instalación)
- [Uso Rápido](#-uso-rápido)
- [API](#-api)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

## ✨ Características

### Funcionalidades Base
- 📊 **Dashboard Público**: Muestra horarios y rankings en tiempo real
- 🎯 **Constructor de Torneos Flexible**: Soporta Swiss, eliminación simple y round-robin
- 🖱️ **Interfaz Drag & Drop**: Arrastra partidos entre canchas y horarios
- 📈 **Rankings Personalizables**: Sistema de puntos configurable
- 👥 **Gestión de Equipos y Jugadores**: Importación masiva vía CSV
- 🏟️ **Gestión de Canchas**: Control de múltiples canchas simultáneas

### 🆕 Nuevas Funcionalidades (Edición Hispanohablante)

#### 👨‍⚖️ **Sistema Completo de Árbitros**
- Registro y gestión de árbitros con niveles de certificación
- Asignación de disponibilidad por torneo
- Múltiples árbitros por partido con diferentes roles
- Detección automática de conflictos de horarios
- Verificación de disponibilidad en tiempo real

#### ⏰ **Scheduling Avanzado con Slots de Tiempo**
- Creación masiva de slots de tiempo configurables
- Duración y descansos personalizables
- Exclusión de días específicos
- Vista de calendario con ocupación
- Asignación flexible de partidos a slots
- Optimización automática de horarios (próximamente)

#### 🌐 **API REST Completa**
- 50+ endpoints documentados
- Autenticación OAuth2
- Paginación y filtros avanzados
- Cliente Python de ejemplo incluido
- Documentación completa en español

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│   Frontend      │────▶│   Backend API   │────▶│   PostgreSQL    │
│   (React/Next)  │     │   (FastAPI)     │     │   Database      │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                        │
        ▼                       ▼                        ▼
   [Dashboard]            [API REST]              [Persistencia]
   - Visualización        - Lógica de             - Torneos
   - Drag & Drop           negocio               - Equipos
   - Rankings             - Validación            - Árbitros
                         - Auth                   - Partidos
                                                  - Slots tiempo
```

## 🚀 Instalación

### Requisitos Previos
- Python 3.10+
- PostgreSQL 14+
- Node.js 18+ (para el frontend)
- pip o pipenv

### 1. Clonar el Repositorio
```bash
git clone https://github.com/evroon/bracket.git
cd bracket
```

### 2. Configurar Backend

#### Opción A: Con Docker
```bash
docker-compose up -d
```

#### Opción B: Instalación Manual
```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración de base de datos

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn bracket.app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Configurar Frontend (Opcional)
```bash
cd frontend
npm install
npm run dev
```

## 💻 Uso Rápido

### 1. Acceder a la Documentación Interactiva
Abre tu navegador en: `http://localhost:8000/docs`

### 2. Autenticación
```python
import requests

# Obtener token
response = requests.post(
    "http://localhost:8000/token",
    data={
        "username": "admin@ejemplo.com",
        "password": "tu_password"
    }
)
token = response.json()["access_token"]
```

### 3. Crear un Torneo con Árbitros
```python
# Usar el cliente de ejemplo
from examples.api_client_example import TournamentAPIClient

client = TournamentAPIClient(
    "http://localhost:8000",
    "admin@ejemplo.com",
    "password"
)

# Crear torneo
torneo = client.crear_torneo(
    "Copa Estrella Blanca 2024",
    club_id=1,
    fecha_inicio=datetime.now()
)

# Registrar árbitros
arbitro = client.registrar_arbitro(
    "Juan Pérez",
    "juan@ejemplo.com",
    "Nacional"
)

# Crear slots de tiempo
client.crear_slots_masivos(
    tournament_id=torneo["id"],
    court_ids=[1, 2, 3],
    fecha_inicio=datetime.now(),
    fecha_fin=datetime.now() + timedelta(days=3)
)
```

## 📚 API

### Endpoints Principales

#### Torneos
- `POST /tournaments` - Crear torneo
- `GET /tournaments` - Listar torneos
- `GET /tournaments/{id}` - Obtener torneo

#### Árbitros
- `POST /referees` - Registrar árbitro
- `GET /referees` - Listar árbitros
- `POST /tournaments/{id}/referees/{referee_id}` - Asignar árbitro a torneo
- `POST /matches/{id}/referees/{referee_id}` - Asignar árbitro a partido
- `GET /tournaments/{id}/referees/available` - Verificar disponibilidad

#### Slots de Tiempo
- `POST /tournaments/{id}/time-slots` - Crear slot individual
- `POST /tournaments/{id}/time-slots/bulk` - Crear slots masivos
- `GET /tournaments/{id}/time-slots` - Listar slots
- `POST /time-slots/{id}/assign-match` - Asignar partido a slot
- `GET /tournaments/{id}/schedule-availability` - Ver disponibilidad

#### Equipos y Partidos
- `POST /tournaments/{id}/teams` - Registrar equipo
- `POST /tournaments/{id}/matches` - Crear partido
- `PUT /tournaments/{id}/matches/{id}` - Actualizar resultado
- `POST /tournaments/{id}/schedule_matches` - Auto-programar partidos

[Ver documentación completa →](./backend/API_DOCUMENTATION_ES.md)

## 📁 Estructura del Proyecto

```
bracket/
├── backend/
│   ├── bracket/
│   │   ├── app.py              # Aplicación FastAPI principal
│   │   ├── models/
│   │   │   └── db/
│   │   │       ├── referee.py  # 🆕 Modelo de árbitros
│   │   │       ├── time_slot.py # 🆕 Modelo de slots
│   │   │       └── ...
│   │   ├── routes/
│   │   │   ├── referees.py     # 🆕 Endpoints de árbitros
│   │   │   ├── time_slots.py   # 🆕 Endpoints de scheduling
│   │   │   └── ...
│   │   ├── sql/
│   │   │   ├── referees.py     # 🆕 Queries de árbitros
│   │   │   ├── time_slots.py   # 🆕 Queries de slots
│   │   │   └── ...
│   │   └── schema.py           # Definición de tablas
│   ├── alembic/
│   │   └── versions/           # Migraciones de BD
│   ├── examples/
│   │   └── api_client_example.py # 🆕 Cliente Python de ejemplo
│   └── API_DOCUMENTATION_ES.md # 🆕 Documentación en español
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```env
# Base de datos
DATABASE_URL=postgresql://user:password@localhost/bracket

# Autenticación
SECRET_KEY=tu-clave-secreta-super-segura
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Configuración de torneos
DEFAULT_MATCH_DURATION=90
DEFAULT_MATCH_MARGIN=15
MAX_MATCHES_PER_DAY=10
```

### Migraciones de Base de Datos
```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

## 🧪 Testing

```bash
cd backend

# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=bracket

# Tests específicos
pytest tests/integration_tests/api/test_referees.py
```

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea tu rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: nueva característica'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Guías de Contribución
- Sigue PEP 8 para código Python
- Usa type hints cuando sea posible
- Incluye tests para nuevas funcionalidades
- Actualiza la documentación

## 📈 Roadmap

- [x] Sistema de árbitros
- [x] Slots de tiempo flexibles
- [x] API REST completa
- [x] Documentación en español
- [ ] Optimización automática de horarios
- [ ] Notificaciones push
- [ ] App móvil para árbitros
- [ ] Integración con calendarios externos
- [ ] Sistema de pagos integrado
- [ ] Estadísticas avanzadas

## 👥 Créditos

### Proyecto Original
- **Bracket** por [Erik Vroon](https://github.com/evroon) y colaboradores
- Licencia: AGPL-3.0

### Adaptación Hispanohablante
- Sistema de árbitros y scheduling avanzado
- API extendida con 30+ nuevos endpoints
- Documentación completa en español
- Cliente Python de ejemplo

## 📄 Licencia

Este proyecto está licenciado bajo AGPL-3.0 - ver el archivo [LICENSE](LICENSE) para detalles.

---

<div align="center">

**¿Encontraste útil este proyecto?** ⭐ Dale una estrella en GitHub

[Reportar Bug](https://github.com/evroon/bracket/issues) • [Solicitar Feature](https://github.com/evroon/bracket/issues) • [Documentación](./backend/API_DOCUMENTATION_ES.md)

</div>
