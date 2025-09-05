"""
Modelo de datos para Árbitros (Referees)
"""
from heliclockter import datetime_utc
from pydantic import BaseModel

from bracket.models.db.shared import BaseModelORM
from bracket.utils.id_types import RefereeId, TournamentId


class RefereeInsertable(BaseModelORM):
    """Modelo base para insertar un árbitro"""
    name: str
    email: str | None = None
    phone: str | None = None
    certification_level: str | None = None  # Nivel de certificación (ej: Nacional, Regional, Local)
    created: datetime_utc
    active: bool = True
    notes: str | None = None


class Referee(RefereeInsertable):
    """Modelo completo de árbitro con ID"""
    id: RefereeId


class RefereeBody(BaseModelORM):
    """Modelo para crear/actualizar árbitro desde API"""
    name: str
    email: str | None = None
    phone: str | None = None
    certification_level: str | None = None
    active: bool = True
    notes: str | None = None


class RefereeAvailability(BaseModelORM):
    """Disponibilidad de un árbitro para un torneo específico"""
    referee_id: RefereeId
    tournament_id: TournamentId
    available_from: datetime_utc
    available_to: datetime_utc
    max_matches_per_day: int = 5
    preferred_courts: list[str] = []  # IDs de canchas preferidas
    notes: str | None = None


class RefereeAssignment(BaseModelORM):
    """Asignación de árbitro a un partido"""
    referee_id: RefereeId
    match_id: int  # MatchId
    role: str = "main"  # main, assistant, line_judge, etc.
    confirmed: bool = False
    notes: str | None = None


class RefereeWithAssignments(Referee):
    """Árbitro con sus asignaciones"""
    assignments: list[RefereeAssignment] = []
    availability: list[RefereeAvailability] = []


class RefereeScheduleConflict(BaseModel):
    """Conflicto de horario para un árbitro"""
    referee_id: RefereeId
    conflict_type: str  # "overlap", "too_many_matches", "not_available"
    match_ids: list[int]
    description: str
