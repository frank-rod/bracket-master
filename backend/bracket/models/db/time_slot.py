"""
Modelo de datos para slots de tiempo mejorados
"""
from heliclockter import datetime_utc
from pydantic import BaseModel

from bracket.models.db.shared import BaseModelORM
from bracket.utils.id_types import CourtId, MatchId, TimeSlotId, TournamentId


class TimeSlotInsertable(BaseModelORM):
    """Modelo base para insertar un slot de tiempo"""
    tournament_id: TournamentId
    court_id: CourtId
    start_time: datetime_utc
    end_time: datetime_utc
    is_available: bool = True
    match_id: MatchId | None = None


class TimeSlot(TimeSlotInsertable):
    """Modelo completo de slot de tiempo con ID"""
    id: TimeSlotId


class TimeSlotBody(BaseModelORM):
    """Modelo para crear/actualizar slot de tiempo desde API"""
    court_id: CourtId
    start_time: datetime_utc
    end_time: datetime_utc
    is_available: bool = True


class TimeSlotWithMatch(TimeSlot):
    """Slot de tiempo con información del partido asignado"""
    match: dict | None = None  # Información básica del partido


class TimeSlotAvailability(BaseModel):
    """Disponibilidad de slots de tiempo para un torneo"""
    tournament_id: TournamentId
    date: datetime_utc
    available_slots: list[TimeSlot]
    occupied_slots: list[TimeSlotWithMatch]
    total_slots: int
    available_count: int
    occupied_count: int


class TimeSlotBulkCreate(BaseModelORM):
    """Modelo para crear múltiples slots de tiempo"""
    tournament_id: TournamentId
    court_ids: list[CourtId]
    start_date: datetime_utc
    end_date: datetime_utc
    slot_duration_minutes: int = 30  # Duración de cada slot
    break_duration_minutes: int = 5  # Descanso entre slots
    daily_start_time: str = "09:00"  # Hora de inicio diaria (HH:MM)
    daily_end_time: str = "21:00"  # Hora de fin diaria (HH:MM)
    exclude_days: list[int] = []  # Días de la semana a excluir (0=Lunes, 6=Domingo)


class TimeSlotConflict(BaseModel):
    """Conflicto de horario para un slot de tiempo"""
    slot_id: TimeSlotId
    conflict_type: str  # "overlap", "court_unavailable", "referee_unavailable"
    description: str
    conflicting_matches: list[MatchId] = []


class ScheduleOptimizationRequest(BaseModelORM):
    """Solicitud para optimizar el calendario de partidos"""
    tournament_id: TournamentId
    optimize_for: str = "minimal_conflicts"  # minimal_conflicts, referee_availability, court_usage
    constraints: dict = {}  # Restricciones adicionales
    
    
class ScheduleSuggestion(BaseModel):
    """Sugerencia de horario para un partido"""
    match_id: MatchId
    suggested_slots: list[TimeSlot]
    referee_availability: dict  # Disponibilidad de árbitros para cada slot
    conflict_score: float  # Puntuación de conflictos (menor es mejor)
    recommendation_reason: str
