"""
Endpoints API para gestión de slots de tiempo y scheduling mejorado
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from heliclockter import datetime_utc

from bracket.models.db.time_slot import (
    TimeSlotBody,
    TimeSlotBulkCreate,
    ScheduleOptimizationRequest,
)
from bracket.models.db.user import UserPublic
from bracket.routes.auth import user_authenticated_for_tournament
from bracket.routes.models import SuccessResponse
from bracket.sql.time_slots import (
    create_time_slot,
    get_time_slot_by_id,
    get_time_slots_for_tournament,
    get_time_slots_with_matches,
    update_time_slot,
    assign_match_to_slot,
    release_slot,
    delete_time_slot,
    bulk_create_time_slots,
    check_slot_conflicts,
    get_next_available_slot,
    optimize_schedule,
)
from bracket.utils.id_types import CourtId, MatchId, TimeSlotId, TournamentId

router = APIRouter()


# Endpoints CRUD básicos para slots de tiempo
@router.post("/tournaments/{tournament_id}/time-slots")
async def create_new_time_slot(
    tournament_id: TournamentId,
    slot: TimeSlotBody,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Crear un nuevo slot de tiempo para un torneo"""
    # Verificar conflictos
    conflicts = await check_slot_conflicts(
        tournament_id,
        slot.court_id,
        slot.start_time,
        slot.end_time,
    )
    
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El slot de tiempo entra en conflicto con {len(conflicts)} slot(s) existente(s)",
        )
    
    return await create_time_slot(tournament_id, slot)


@router.post("/tournaments/{tournament_id}/time-slots/bulk")
async def create_time_slots_bulk(
    tournament_id: TournamentId,
    bulk_request: TimeSlotBulkCreate,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Crear múltiples slots de tiempo de forma masiva"""
    bulk_request.tournament_id = tournament_id
    created_slots = await bulk_create_time_slots(bulk_request)
    
    return {
        "message": f"Se crearon {len(created_slots)} slots de tiempo exitosamente",
        "created_count": len(created_slots),
        "slots": created_slots[:10],  # Retornar solo los primeros 10 como muestra
    }


@router.get("/tournaments/{tournament_id}/time-slots")
async def get_tournament_time_slots(
    tournament_id: TournamentId,
    court_id: CourtId | None = Query(None, description="Filtrar por cancha"),
    date: datetime_utc | None = Query(None, description="Filtrar por fecha"),
    only_available: bool = Query(False, description="Mostrar solo slots disponibles"),
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener todos los slots de tiempo de un torneo con filtros opcionales"""
    return await get_time_slots_for_tournament(
        tournament_id,
        court_id,
        date,
        only_available,
    )


@router.get("/tournaments/{tournament_id}/time-slots/with-matches")
async def get_time_slots_with_match_info(
    tournament_id: TournamentId,
    date: datetime_utc | None = Query(None, description="Filtrar por fecha"),
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener slots de tiempo con información de partidos asignados"""
    return await get_time_slots_with_matches(tournament_id, date)


@router.get("/tournaments/{tournament_id}/time-slots/next-available")
async def get_next_available_time_slot(
    tournament_id: TournamentId,
    court_id: CourtId | None = Query(None, description="Filtrar por cancha"),
    after_time: datetime_utc | None = Query(None, description="Buscar después de esta hora"),
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener el siguiente slot de tiempo disponible"""
    next_slot = await get_next_available_slot(tournament_id, court_id, after_time)
    
    if not next_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron slots disponibles con los criterios especificados",
        )
    
    return next_slot


@router.get("/time-slots/{slot_id}")
async def get_time_slot(
    slot_id: TimeSlotId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener información de un slot de tiempo específico"""
    slot = await get_time_slot_by_id(slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot de tiempo con ID {slot_id} no encontrado",
        )
    return slot


@router.put("/time-slots/{slot_id}")
async def update_time_slot_info(
    slot_id: TimeSlotId,
    updates: dict,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Actualizar información de un slot de tiempo"""
    # Verificar que el slot existe
    existing_slot = await get_time_slot_by_id(slot_id)
    if not existing_slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot de tiempo con ID {slot_id} no encontrado",
        )
    
    # Si se está cambiando el horario, verificar conflictos
    if "start_time" in updates or "end_time" in updates:
        conflicts = await check_slot_conflicts(
            existing_slot.tournament_id,
            existing_slot.court_id,
            updates.get("start_time", existing_slot.start_time),
            updates.get("end_time", existing_slot.end_time),
            exclude_slot_id=slot_id,
        )
        
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El nuevo horario entra en conflicto con {len(conflicts)} slot(s)",
            )
    
    updated_slot = await update_time_slot(slot_id, updates)
    return updated_slot


@router.delete("/time-slots/{slot_id}")
async def delete_time_slot_by_id(
    slot_id: TimeSlotId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
) -> SuccessResponse:
    """Eliminar un slot de tiempo"""
    # Verificar que el slot no tenga un partido asignado
    slot = await get_time_slot_by_id(slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot de tiempo con ID {slot_id} no encontrado",
        )
    
    if slot.match_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar un slot con un partido asignado",
        )
    
    deleted = await delete_time_slot(slot_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar el slot de tiempo",
        )
    
    return SuccessResponse()


# Endpoints para asignación de partidos a slots
@router.post("/time-slots/{slot_id}/assign-match")
async def assign_match_to_time_slot(
    slot_id: TimeSlotId,
    match_id: MatchId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Asignar un partido a un slot de tiempo"""
    # Verificar que el slot existe y está disponible
    slot = await get_time_slot_by_id(slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot de tiempo con ID {slot_id} no encontrado",
        )
    
    if not slot.is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slot de tiempo no está disponible",
        )
    
    if slot.match_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slot ya tiene un partido asignado",
        )
    
    updated_slot = await assign_match_to_slot(slot_id, match_id)
    return updated_slot


@router.post("/time-slots/{slot_id}/release")
async def release_time_slot(
    slot_id: TimeSlotId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Liberar un slot de tiempo (quitar partido asignado)"""
    slot = await get_time_slot_by_id(slot_id)
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Slot de tiempo con ID {slot_id} no encontrado",
        )
    
    if not slot.match_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El slot no tiene ningún partido asignado",
        )
    
    updated_slot = await release_slot(slot_id)
    return updated_slot


# Endpoint para optimización de calendario
@router.post("/tournaments/{tournament_id}/optimize-schedule")
async def optimize_tournament_schedule(
    tournament_id: TournamentId,
    optimization_request: ScheduleOptimizationRequest,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """
    Optimizar el calendario de partidos del torneo
    
    Tipos de optimización disponibles:
    - minimal_conflicts: Minimizar conflictos de horarios
    - referee_availability: Optimizar según disponibilidad de árbitros
    - court_usage: Maximizar uso eficiente de canchas
    """
    optimization_request.tournament_id = tournament_id
    result = await optimize_schedule(
        tournament_id,
        optimization_request.optimize_for,
    )
    
    return result


# Endpoint para obtener disponibilidad general
@router.get("/tournaments/{tournament_id}/schedule-availability")
async def get_schedule_availability(
    tournament_id: TournamentId,
    date: datetime_utc,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener resumen de disponibilidad de horarios para una fecha"""
    all_slots = await get_time_slots_for_tournament(tournament_id, date=date)
    available_slots = [s for s in all_slots if s.is_available]
    occupied_slots = [s for s in all_slots if not s.is_available]
    
    # Agrupar por cancha
    slots_by_court = {}
    for slot in all_slots:
        if slot.court_id not in slots_by_court:
            slots_by_court[slot.court_id] = {
                "available": [],
                "occupied": [],
            }
        
        if slot.is_available:
            slots_by_court[slot.court_id]["available"].append(slot)
        else:
            slots_by_court[slot.court_id]["occupied"].append(slot)
    
    return {
        "tournament_id": tournament_id,
        "date": date,
        "total_slots": len(all_slots),
        "available_count": len(available_slots),
        "occupied_count": len(occupied_slots),
        "availability_percentage": (len(available_slots) / len(all_slots) * 100) if all_slots else 0,
        "slots_by_court": slots_by_court,
    }

