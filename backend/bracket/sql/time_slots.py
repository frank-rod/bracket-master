"""
Funciones SQL para manejar slots de tiempo
"""
from datetime import datetime, time, timedelta
from heliclockter import datetime_utc

from bracket.database import database
from bracket.models.db.time_slot import (
    TimeSlot,
    TimeSlotBody,
    TimeSlotBulkCreate,
    TimeSlotInsertable,
    TimeSlotWithMatch,
)
from bracket.schema import time_slots, matches
from bracket.utils.id_types import CourtId, MatchId, TimeSlotId, TournamentId


async def create_time_slot(
    tournament_id: TournamentId,
    slot: TimeSlotBody,
) -> TimeSlot:
    """Crear un nuevo slot de tiempo"""
    query = (
        time_slots.insert()
        .values(
            tournament_id=tournament_id,
            court_id=slot.court_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
            match_id=None,
        )
        .returning(time_slots)
    )
    result = await database.fetch_one(query)
    assert result is not None
    return TimeSlot.model_validate(result)


async def get_time_slot_by_id(slot_id: TimeSlotId) -> TimeSlot | None:
    """Obtener un slot de tiempo por ID"""
    query = time_slots.select().where(time_slots.c.id == slot_id)
    result = await database.fetch_one(query)
    return TimeSlot.model_validate(result) if result else None


async def get_time_slots_for_tournament(
    tournament_id: TournamentId,
    court_id: CourtId | None = None,
    date: datetime_utc | None = None,
    only_available: bool = False,
) -> list[TimeSlot]:
    """Obtener slots de tiempo para un torneo con filtros opcionales"""
    query = time_slots.select().where(time_slots.c.tournament_id == tournament_id)
    
    if court_id:
        query = query.where(time_slots.c.court_id == court_id)
    
    if date:
        # Filtrar por fecha (ignorando la hora)
        start_of_day = datetime.combine(date.date(), time.min).replace(tzinfo=date.tzinfo)
        end_of_day = datetime.combine(date.date(), time.max).replace(tzinfo=date.tzinfo)
        query = query.where(
            (time_slots.c.start_time >= start_of_day) &
            (time_slots.c.start_time <= end_of_day)
        )
    
    if only_available:
        query = query.where(time_slots.c.is_available == True)
    
    query = query.order_by(time_slots.c.start_time, time_slots.c.court_id)
    
    result = await database.fetch_all(query)
    return [TimeSlot.model_validate(row) for row in result]


async def get_time_slots_with_matches(
    tournament_id: TournamentId,
    date: datetime_utc | None = None,
) -> list[TimeSlotWithMatch]:
    """Obtener slots de tiempo con información de partidos asignados"""
    query = (
        time_slots.select()
        .add_columns(
            matches.c.id.label("match_id_info"),
            matches.c.stage_item_input1_score,
            matches.c.stage_item_input2_score,
        )
        .select_from(
            time_slots.outerjoin(
                matches,
                time_slots.c.match_id == matches.c.id,
            )
        )
        .where(time_slots.c.tournament_id == tournament_id)
    )
    
    if date:
        start_of_day = datetime.combine(date.date(), time.min).replace(tzinfo=date.tzinfo)
        end_of_day = datetime.combine(date.date(), time.max).replace(tzinfo=date.tzinfo)
        query = query.where(
            (time_slots.c.start_time >= start_of_day) &
            (time_slots.c.start_time <= end_of_day)
        )
    
    query = query.order_by(time_slots.c.start_time, time_slots.c.court_id)
    
    result = await database.fetch_all(query)
    slots = []
    
    for row in result:
        slot = TimeSlotWithMatch.model_validate(row)
        if row["match_id_info"]:
            slot.match = {
                "id": row["match_id_info"],
                "score1": row["stage_item_input1_score"],
                "score2": row["stage_item_input2_score"],
            }
        slots.append(slot)
    
    return slots


async def update_time_slot(
    slot_id: TimeSlotId,
    updates: dict,
) -> TimeSlot | None:
    """Actualizar un slot de tiempo"""
    query = (
        time_slots.update()
        .where(time_slots.c.id == slot_id)
        .values(**updates)
        .returning(time_slots)
    )
    result = await database.fetch_one(query)
    return TimeSlot.model_validate(result) if result else None


async def assign_match_to_slot(
    slot_id: TimeSlotId,
    match_id: MatchId,
) -> TimeSlot | None:
    """Asignar un partido a un slot de tiempo"""
    return await update_time_slot(
        slot_id,
        {"match_id": match_id, "is_available": False}
    )


async def release_slot(slot_id: TimeSlotId) -> TimeSlot | None:
    """Liberar un slot de tiempo (quitar partido asignado)"""
    return await update_time_slot(
        slot_id,
        {"match_id": None, "is_available": True}
    )


async def delete_time_slot(slot_id: TimeSlotId) -> bool:
    """Eliminar un slot de tiempo"""
    query = time_slots.delete().where(time_slots.c.id == slot_id)
    result = await database.execute(query)
    return result > 0


async def bulk_create_time_slots(
    bulk_request: TimeSlotBulkCreate,
) -> list[TimeSlot]:
    """Crear múltiples slots de tiempo de forma masiva"""
    created_slots = []
    
    # Parsear horarios diarios
    daily_start = datetime.strptime(bulk_request.daily_start_time, "%H:%M").time()
    daily_end = datetime.strptime(bulk_request.daily_end_time, "%H:%M").time()
    
    # Iterar sobre cada día en el rango
    current_date = bulk_request.start_date.date()
    end_date = bulk_request.end_date.date()
    
    while current_date <= end_date:
        # Verificar si el día debe ser excluido
        if current_date.weekday() in bulk_request.exclude_days:
            current_date += timedelta(days=1)
            continue
        
        # Para cada cancha
        for court_id in bulk_request.court_ids:
            # Crear slots para el día
            current_time = datetime.combine(
                current_date,
                daily_start,
                tzinfo=bulk_request.start_date.tzinfo
            )
            
            end_time_for_day = datetime.combine(
                current_date,
                daily_end,
                tzinfo=bulk_request.start_date.tzinfo
            )
            
            while current_time < end_time_for_day:
                slot_end = current_time + timedelta(minutes=bulk_request.slot_duration_minutes)
                
                # No crear slots que excedan el horario diario
                if slot_end > end_time_for_day:
                    break
                
                # Crear el slot
                slot_data = TimeSlotInsertable(
                    tournament_id=bulk_request.tournament_id,
                    court_id=court_id,
                    start_time=current_time,
                    end_time=slot_end,
                    is_available=True,
                    match_id=None,
                )
                
                query = (
                    time_slots.insert()
                    .values(**slot_data.model_dump())
                    .returning(time_slots)
                )
                result = await database.fetch_one(query)
                if result:
                    created_slots.append(TimeSlot.model_validate(result))
                
                # Avanzar al siguiente slot (incluyendo tiempo de descanso)
                current_time = slot_end + timedelta(minutes=bulk_request.break_duration_minutes)
        
        # Avanzar al siguiente día
        current_date += timedelta(days=1)
    
    return created_slots


async def check_slot_conflicts(
    tournament_id: TournamentId,
    court_id: CourtId,
    start_time: datetime_utc,
    end_time: datetime_utc,
    exclude_slot_id: TimeSlotId | None = None,
) -> list[TimeSlot]:
    """Verificar conflictos con otros slots de tiempo"""
    query = time_slots.select().where(
        (time_slots.c.tournament_id == tournament_id) &
        (time_slots.c.court_id == court_id) &
        (
            # Slots que se solapan con el rango propuesto
            (
                (time_slots.c.start_time < end_time) &
                (time_slots.c.end_time > start_time)
            )
        )
    )
    
    if exclude_slot_id:
        query = query.where(time_slots.c.id != exclude_slot_id)
    
    result = await database.fetch_all(query)
    return [TimeSlot.model_validate(row) for row in result]


async def get_next_available_slot(
    tournament_id: TournamentId,
    court_id: CourtId | None = None,
    after_time: datetime_utc | None = None,
) -> TimeSlot | None:
    """Obtener el siguiente slot disponible"""
    query = time_slots.select().where(
        (time_slots.c.tournament_id == tournament_id) &
        (time_slots.c.is_available == True)
    )
    
    if court_id:
        query = query.where(time_slots.c.court_id == court_id)
    
    if after_time:
        query = query.where(time_slots.c.start_time > after_time)
    
    query = query.order_by(time_slots.c.start_time).limit(1)
    
    result = await database.fetch_one(query)
    return TimeSlot.model_validate(result) if result else None


async def optimize_schedule(
    tournament_id: TournamentId,
    optimization_type: str = "minimal_conflicts",
) -> dict:
    """
    Optimizar el calendario de partidos según diferentes criterios
    
    TODO: Implementar algoritmo de optimización completo
    """
    # Por ahora, retornar un placeholder
    return {
        "tournament_id": tournament_id,
        "optimization_type": optimization_type,
        "status": "pending_implementation",
        "message": "La optimización de calendario está pendiente de implementación completa",
        "suggestions": [],
    }

