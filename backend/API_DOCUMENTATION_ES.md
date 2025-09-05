# 📚 Documentación API - Sistema de Gestión de Torneos

## 🎯 Descripción General

Esta API REST permite la gestión completa de torneos deportivos, incluyendo:
- Gestión de equipos y jugadores
- Programación de partidos con slots de tiempo flexibles
- Asignación y gestión de árbitros
- Seguimiento de resultados y rankings
- Dashboard público para visualización

## 🔐 Autenticación

La API utiliza autenticación basada en tokens OAuth2. Para acceder a los endpoints protegidos:

1. Obtener token de acceso mediante `/token` con credenciales
2. Incluir el token en el header: `Authorization: Bearer {token}`

## 📋 Endpoints Principales

### 🏆 Torneos (`/tournaments`)

#### Crear Torneo
```http
POST /tournaments
```
**Body:**
```json
{
  "name": "Copa Estrella Blanca 2024",
  "start_time": "2024-03-01T09:00:00Z",
  "club_id": 1,
  "dashboard_public": true,
  "duration_minutes": 90,
  "margin_minutes": 15
}
```

#### Listar Torneos
```http
GET /tournaments?filter=OPEN
```
Filtros disponibles: `ALL`, `OPEN`, `ARCHIVED`

#### Obtener Torneo Específico
```http
GET /tournaments/{tournament_id}
```

### 👥 Equipos (`/teams`)

#### Registrar Equipo
```http
POST /tournaments/{tournament_id}/teams
```
**Body:**
```json
{
  "name": "Real Madrid",
  "active": true,
  "logo_path": "/logos/real_madrid.png"
}
```

#### Listar Equipos del Torneo
```http
GET /tournaments/{tournament_id}/teams
```

### 👨‍⚖️ Árbitros (`/referees`)

#### Registrar Árbitro
```http
POST /referees
```
**Body:**
```json
{
  "name": "Juan Pérez",
  "email": "juan.perez@ejemplo.com",
  "phone": "+34 600 123 456",
  "certification_level": "Nacional",
  "active": true,
  "notes": "Especializado en fútbol profesional"
}
```

#### Listar Árbitros
```http
GET /referees?active_only=true&limit=25&offset=0
```

#### Asignar Árbitro a Torneo
```http
POST /tournaments/{tournament_id}/referees/{referee_id}
```
**Body:**
```json
{
  "available_from": "2024-03-01T08:00:00Z",
  "available_to": "2024-03-01T22:00:00Z",
  "max_matches_per_day": 3,
  "preferred_courts": [1, 2, 3],
  "notes": "Disponible solo fines de semana"
}
```

#### Asignar Árbitro a Partido
```http
POST /matches/{match_id}/referees/{referee_id}?role=main&confirmed=true
```
Roles disponibles: `main`, `assistant`, `line_judge`, `video_referee`

#### Obtener Árbitros de un Partido
```http
GET /matches/{match_id}/referees
```

#### Verificar Disponibilidad de Árbitros
```http
GET /tournaments/{tournament_id}/referees/available?start_time=2024-03-01T10:00:00Z&end_time=2024-03-01T12:00:00Z
```

### ⏰ Slots de Tiempo (`/time-slots`)

#### Crear Slot Individual
```http
POST /tournaments/{tournament_id}/time-slots
```
**Body:**
```json
{
  "court_id": 1,
  "start_time": "2024-03-01T10:00:00Z",
  "end_time": "2024-03-01T11:30:00Z",
  "is_available": true
}
```

#### Crear Slots Masivos
```http
POST /tournaments/{tournament_id}/time-slots/bulk
```
**Body:**
```json
{
  "court_ids": [1, 2, 3],
  "start_date": "2024-03-01T00:00:00Z",
  "end_date": "2024-03-07T23:59:59Z",
  "slot_duration_minutes": 90,
  "break_duration_minutes": 15,
  "daily_start_time": "09:00",
  "daily_end_time": "21:00",
  "exclude_days": [0, 6]
}
```
*Nota: exclude_days usa 0=Lunes, 6=Domingo*

#### Listar Slots de Tiempo
```http
GET /tournaments/{tournament_id}/time-slots?court_id=1&date=2024-03-01&only_available=true
```

#### Obtener Slots con Información de Partidos
```http
GET /tournaments/{tournament_id}/time-slots/with-matches?date=2024-03-01
```

#### Siguiente Slot Disponible
```http
GET /tournaments/{tournament_id}/time-slots/next-available?court_id=1&after_time=2024-03-01T14:00:00Z
```

#### Asignar Partido a Slot
```http
POST /time-slots/{slot_id}/assign-match
```
**Body:**
```json
{
  "match_id": 123
}
```

#### Liberar Slot
```http
POST /time-slots/{slot_id}/release
```

#### Obtener Disponibilidad del Calendario
```http
GET /tournaments/{tournament_id}/schedule-availability?date=2024-03-01
```

### 🏟️ Canchas (`/courts`)

#### Crear Cancha
```http
POST /tournaments/{tournament_id}/courts
```
**Body:**
```json
{
  "name": "Cancha Principal"
}
```

#### Listar Canchas
```http
GET /tournaments/{tournament_id}/courts
```

### ⚽ Partidos (`/matches`)

#### Crear Partido
```http
POST /tournaments/{tournament_id}/matches
```
**Body:**
```json
{
  "round_id": 1,
  "court_id": 1,
  "stage_item_input1_id": 1,
  "stage_item_input2_id": 2
}
```

#### Actualizar Resultado
```http
PUT /tournaments/{tournament_id}/matches/{match_id}
```
**Body:**
```json
{
  "stage_item_input1_score": 3,
  "stage_item_input2_score": 1,
  "custom_duration_minutes": 95
}
```

#### Reprogramar Partido
```http
POST /tournaments/{tournament_id}/matches/{match_id}/reschedule
```
**Body:**
```json
{
  "old_court_id": 1,
  "old_position": 0,
  "new_court_id": 2,
  "new_position": 3
}
```

#### Obtener Próximos Partidos Sugeridos (Swiss)
```http
GET /tournaments/{tournament_id}/stage_items/{stage_item_id}/upcoming_matches?elo_diff_threshold=200&limit=10
```

### 📊 Rankings (`/rankings`)

#### Obtener Rankings del Torneo
```http
GET /tournaments/{tournament_id}/rankings
```

#### Actualizar Configuración de Ranking
```http
PUT /tournaments/{tournament_id}/rankings/{ranking_id}
```
**Body:**
```json
{
  "win_points": 3.0,
  "draw_points": 1.0,
  "loss_points": 0.0,
  "add_score_points": true
}
```

## 🔄 Flujo de Trabajo Típico

### 1. Configuración Inicial del Torneo

1. **Crear Club** (si no existe)
2. **Crear Torneo** con configuración básica
3. **Crear Canchas** disponibles
4. **Registrar Árbitros** en el sistema
5. **Asignar Árbitros al Torneo** con su disponibilidad

### 2. Preparación de Partidos

1. **Registrar Equipos** participantes
2. **Crear Etapas** (stages) del torneo
3. **Generar Slots de Tiempo** masivamente
4. **Crear Rondas y Partidos**

### 3. Durante el Torneo

1. **Asignar Partidos a Slots** de tiempo
2. **Asignar Árbitros a Partidos**
3. **Actualizar Resultados** conforme se juegan
4. **Consultar Rankings** actualizados

### 4. Gestión de Cambios

- **Reprogramar Partidos** si es necesario
- **Cambiar Árbitros** asignados
- **Liberar/Reasignar Slots** de tiempo

## 🛠️ Características Avanzadas

### Optimización de Calendario
```http
POST /tournaments/{tournament_id}/optimize-schedule
```
**Body:**
```json
{
  "optimize_for": "minimal_conflicts",
  "constraints": {
    "max_matches_per_day_per_team": 2,
    "min_rest_between_matches": 120
  }
}
```
Tipos de optimización:
- `minimal_conflicts`: Minimizar conflictos de horarios
- `referee_availability`: Optimizar según disponibilidad de árbitros
- `court_usage`: Maximizar uso eficiente de canchas

### Detección de Conflictos de Árbitros
```http
GET /referees/{referee_id}/conflicts?tournament_id=1&date=2024-03-01
```

## 📝 Modelos de Respuesta

### Respuesta Exitosa Genérica
```json
{
  "success": true
}
```

### Respuesta de Error
```json
{
  "detail": "Descripción del error",
  "status_code": 400
}
```

### Paginación
La mayoría de endpoints de listado soportan paginación:
- `limit`: Número máximo de resultados (1-100)
- `offset`: Número de resultados a saltar
- `sort_by`: Campo por el cual ordenar
- `sort_direction`: `asc` o `desc`

## 🌍 Internacionalización

La API soporta múltiples idiomas. Los mensajes de error y respuestas pueden ser localizados según el header `Accept-Language`.

## 📊 Dashboard Público

Los torneos pueden tener un dashboard público accesible sin autenticación en:
```
GET /tournaments/{tournament_id}/dashboard
```

## 🔒 Consideraciones de Seguridad

- Todos los endpoints requieren autenticación excepto el dashboard público
- Los tokens expiran después de 30 minutos
- Las contraseñas se almacenan hasheadas con bcrypt
- CORS configurado para dominios específicos en producción

## 📈 Límites de Rate

- 100 requests por minuto por usuario autenticado
- 20 requests por minuto para endpoints públicos

## 🐛 Debugging

Para obtener información detallada de errores en desarrollo, incluir header:
```
X-Debug-Mode: true
```

## 📞 Soporte

Para preguntas o problemas con la API:
- GitHub Issues: [https://github.com/evroon/bracket](https://github.com/evroon/bracket)
- Documentación: [https://docs.bracketapp.nl](https://docs.bracketapp.nl)

---

*Versión API: 1.0.0*  
*Última actualización: Enero 2024*
