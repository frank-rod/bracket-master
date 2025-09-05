"""
Funciones SQL para manejar árbitros
"""
from heliclockter import datetime_utc

from bracket.database import database
from bracket.models.db.referee import (
    Referee,
    RefereeAvailability,
    RefereeAssignment,
    RefereeBody,
    RefereeInsertable,
    RefereeWithAssignments,
)
from bracket.schema import referees, referees_x_matches, referees_x_tournaments
from bracket.utils.id_types import MatchId, RefereeId, TournamentId
from bracket.utils.pagination import PaginationReferees
from bracket.utils.types import dict_without_none


async def create_referee(referee: RefereeBody) -> Referee:
    """Crear un nuevo árbitro"""
    query = (
        referees.insert()
        .values(
            name=referee.name,
            email=referee.email,
            phone=referee.phone,
            certification_level=referee.certification_level,
            active=referee.active,
            notes=referee.notes,
            created=datetime_utc.now(),
        )
        .returning(referees)
    )
    result = await database.fetch_one(query)
    assert result is not None
    return Referee.model_validate(result)


async def get_referee_by_id(referee_id: RefereeId) -> Referee | None:
    """Obtener un árbitro por ID"""
    query = referees.select().where(referees.c.id == referee_id)
    result = await database.fetch_one(query)
    return Referee.model_validate(result) if result else None


async def get_all_referees(
    active_only: bool = False,
    pagination: PaginationReferees | None = None,
) -> list[Referee]:
    """Obtener todos los árbitros con paginación opcional"""
    query = referees.select()
    
    if active_only:
        query = query.where(referees.c.active == True)
    
    query = query.order_by(referees.c.name)
    
    if pagination:
        query = query.limit(pagination.limit).offset(pagination.offset)
    
    result = await database.fetch_all(query)
    return [Referee.model_validate(row) for row in result]


async def update_referee(referee_id: RefereeId, referee_update: RefereeBody) -> Referee | None:
    """Actualizar un árbitro"""
    query = (
        referees.update()
        .where(referees.c.id == referee_id)
        .values(**dict_without_none(**referee_update.model_dump()))
        .returning(referees)
    )
    result = await database.fetch_one(query)
    return Referee.model_validate(result) if result else None


async def delete_referee(referee_id: RefereeId) -> bool:
    """Eliminar un árbitro"""
    query = referees.delete().where(referees.c.id == referee_id)
    result = await database.execute(query)
    return result > 0


# Funciones para disponibilidad de árbitros en torneos
async def add_referee_to_tournament(
    referee_id: RefereeId,
    tournament_id: TournamentId,
    availability: RefereeAvailability,
) -> RefereeAvailability:
    """Agregar un árbitro a un torneo con su disponibilidad"""
    query = (
        referees_x_tournaments.insert()
        .values(
            referee_id=referee_id,
            tournament_id=tournament_id,
            available_from=availability.available_from,
            available_to=availability.available_to,
            max_matches_per_day=availability.max_matches_per_day,
            preferred_courts=availability.preferred_courts,
            notes=availability.notes,
        )
        .returning(referees_x_tournaments)
    )
    result = await database.fetch_one(query)
    assert result is not None
    return RefereeAvailability.model_validate(result)


async def get_referees_for_tournament(tournament_id: TournamentId) -> list[RefereeWithAssignments]:
    """Obtener todos los árbitros disponibles para un torneo"""
    # Primero obtener los árbitros del torneo
    query = (
        referees.select()
        .select_from(
            referees.join(
                referees_x_tournaments,
                referees.c.id == referees_x_tournaments.c.referee_id,
            )
        )
        .where(referees_x_tournaments.c.tournament_id == tournament_id)
        .where(referees.c.active == True)
    )
    
    referees_result = await database.fetch_all(query)
    referees_list = []
    
    for referee_row in referees_result:
        referee = RefereeWithAssignments.model_validate(referee_row)
        
        # Obtener disponibilidad
        avail_query = referees_x_tournaments.select().where(
            (referees_x_tournaments.c.referee_id == referee.id) &
            (referees_x_tournaments.c.tournament_id == tournament_id)
        )
        avail_result = await database.fetch_all(avail_query)
        referee.availability = [RefereeAvailability.model_validate(row) for row in avail_result]
        
        # Obtener asignaciones
        assign_query = referees_x_matches.select().where(
            referees_x_matches.c.referee_id == referee.id
        )
        assign_result = await database.fetch_all(assign_query)
        referee.assignments = [RefereeAssignment.model_validate(row) for row in assign_result]
        
        referees_list.append(referee)
    
    return referees_list


async def get_available_referees_for_time_slot(
    tournament_id: TournamentId,
    start_time: datetime_utc,
    end_time: datetime_utc,
) -> list[Referee]:
    """Obtener árbitros disponibles para un horario específico"""
    # Obtener árbitros que están disponibles en ese rango de tiempo
    query = (
        referees.select()
        .select_from(
            referees.join(
                referees_x_tournaments,
                referees.c.id == referees_x_tournaments.c.referee_id,
            )
        )
        .where(
            (referees_x_tournaments.c.tournament_id == tournament_id) &
            (referees_x_tournaments.c.available_from <= start_time) &
            (referees_x_tournaments.c.available_to >= end_time) &
            (referees.c.active == True)
        )
    )
    
    result = await database.fetch_all(query)
    available_referees = []
    
    for row in result:
        referee = Referee.model_validate(row)
        
        # Verificar que no tenga conflictos con otros partidos en ese horario
        conflict_query = f"""
            SELECT COUNT(*) as count
            FROM referees_x_matches rxm
            JOIN matches m ON rxm.match_id = m.id
            WHERE rxm.referee_id = :referee_id
            AND m.start_time < :end_time
            AND (m.start_time + INTERVAL '1 minute' * (m.duration_minutes + m.margin_minutes)) > :start_time
        """
        
        conflict_result = await database.fetch_one(
            conflict_query,
            {"referee_id": referee.id, "start_time": start_time, "end_time": end_time}
        )
        
        if conflict_result and conflict_result["count"] == 0:
            available_referees.append(referee)
    
    return available_referees


# Funciones para asignación de árbitros a partidos
async def assign_referee_to_match(
    referee_id: RefereeId,
    match_id: MatchId,
    role: str = "main",
    confirmed: bool = False,
    notes: str | None = None,
) -> RefereeAssignment:
    """Asignar un árbitro a un partido"""
    query = (
        referees_x_matches.insert()
        .values(
            referee_id=referee_id,
            match_id=match_id,
            role=role,
            confirmed=confirmed,
            notes=notes,
        )
        .returning(referees_x_matches)
    )
    result = await database.fetch_one(query)
    assert result is not None
    return RefereeAssignment.model_validate(result)


async def get_referees_for_match(match_id: MatchId) -> list[tuple[Referee, RefereeAssignment]]:
    """Obtener todos los árbitros asignados a un partido"""
    query = (
        referees.select()
        .add_columns(
            referees_x_matches.c.role,
            referees_x_matches.c.confirmed,
            referees_x_matches.c.notes.label("assignment_notes"),
        )
        .select_from(
            referees.join(
                referees_x_matches,
                referees.c.id == referees_x_matches.c.referee_id,
            )
        )
        .where(referees_x_matches.c.match_id == match_id)
    )
    
    result = await database.fetch_all(query)
    referees_list = []
    
    for row in result:
        referee = Referee.model_validate(row)
        assignment = RefereeAssignment(
            referee_id=row["id"],
            match_id=match_id,
            role=row["role"],
            confirmed=row["confirmed"],
            notes=row["assignment_notes"],
        )
        referees_list.append((referee, assignment))
    
    return referees_list


async def remove_referee_from_match(referee_id: RefereeId, match_id: MatchId) -> bool:
    """Remover un árbitro de un partido"""
    query = referees_x_matches.delete().where(
        (referees_x_matches.c.referee_id == referee_id) &
        (referees_x_matches.c.match_id == match_id)
    )
    result = await database.execute(query)
    return result > 0


async def update_referee_assignment(
    referee_id: RefereeId,
    match_id: MatchId,
    confirmed: bool | None = None,
    notes: str | None = None,
) -> RefereeAssignment | None:
    """Actualizar la asignación de un árbitro a un partido"""
    update_values = {}
    if confirmed is not None:
        update_values["confirmed"] = confirmed
    if notes is not None:
        update_values["notes"] = notes
    
    if not update_values:
        return None
    
    query = (
        referees_x_matches.update()
        .where(
            (referees_x_matches.c.referee_id == referee_id) &
            (referees_x_matches.c.match_id == match_id)
        )
        .values(**update_values)
        .returning(referees_x_matches)
    )
    result = await database.fetch_one(query)
    return RefereeAssignment.model_validate(result) if result else None

