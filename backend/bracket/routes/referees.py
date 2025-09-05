"""
Endpoints API para gestión de árbitros
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette import status
from heliclockter import datetime_utc

from bracket.models.db.referee import (
    RefereeBody,
    RefereeAvailability,
    RefereeAssignment,
)
from bracket.models.db.user import UserPublic
from bracket.routes.auth import user_authenticated_for_tournament
from bracket.routes.models import SuccessResponse
from bracket.sql.referees import (
    create_referee,
    get_referee_by_id,
    get_all_referees,
    update_referee,
    delete_referee,
    add_referee_to_tournament,
    get_referees_for_tournament,
    get_available_referees_for_time_slot,
    assign_referee_to_match,
    get_referees_for_match,
    remove_referee_from_match,
    update_referee_assignment,
)
from bracket.utils.id_types import MatchId, RefereeId, TournamentId
from bracket.utils.pagination import PaginationReferees

router = APIRouter()


# Endpoints CRUD básicos para árbitros
@router.post("/referees")
async def create_new_referee(
    referee: RefereeBody,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Crear un nuevo árbitro en el sistema"""
    return await create_referee(referee)


@router.get("/referees")
async def get_referees(
    active_only: bool = Query(False, description="Filtrar solo árbitros activos"),
    pagination: PaginationReferees = Depends(),
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener lista de árbitros con paginación"""
    return await get_all_referees(active_only, pagination)


@router.get("/referees/{referee_id}")
async def get_referee(
    referee_id: RefereeId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener información de un árbitro específico"""
    referee = await get_referee_by_id(referee_id)
    if not referee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Árbitro con ID {referee_id} no encontrado",
        )
    return referee


@router.put("/referees/{referee_id}")
async def update_referee_info(
    referee_id: RefereeId,
    referee_update: RefereeBody,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Actualizar información de un árbitro"""
    updated_referee = await update_referee(referee_id, referee_update)
    if not updated_referee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Árbitro con ID {referee_id} no encontrado",
        )
    return updated_referee


@router.delete("/referees/{referee_id}")
async def delete_referee_by_id(
    referee_id: RefereeId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
) -> SuccessResponse:
    """Eliminar un árbitro del sistema"""
    deleted = await delete_referee(referee_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Árbitro con ID {referee_id} no encontrado",
        )
    return SuccessResponse()


# Endpoints para gestión de árbitros en torneos
@router.post("/tournaments/{tournament_id}/referees/{referee_id}")
async def add_referee_availability(
    tournament_id: TournamentId,
    referee_id: RefereeId,
    availability: RefereeAvailability,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Agregar un árbitro a un torneo con su disponibilidad"""
    # Verificar que el árbitro existe
    referee = await get_referee_by_id(referee_id)
    if not referee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Árbitro con ID {referee_id} no encontrado",
        )
    
    return await add_referee_to_tournament(referee_id, tournament_id, availability)


@router.get("/tournaments/{tournament_id}/referees")
async def get_tournament_referees(
    tournament_id: TournamentId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener todos los árbitros disponibles para un torneo"""
    return await get_referees_for_tournament(tournament_id)


@router.get("/tournaments/{tournament_id}/referees/available")
async def get_available_referees(
    tournament_id: TournamentId,
    start_time: datetime_utc,
    end_time: datetime_utc,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener árbitros disponibles para un horario específico"""
    return await get_available_referees_for_time_slot(tournament_id, start_time, end_time)


# Endpoints para asignación de árbitros a partidos
@router.post("/matches/{match_id}/referees/{referee_id}")
async def assign_referee(
    match_id: MatchId,
    referee_id: RefereeId,
    role: str = Query("main", description="Rol del árbitro: main, assistant, line_judge"),
    confirmed: bool = Query(False, description="Si la asignación está confirmada"),
    notes: str | None = Query(None, description="Notas adicionales"),
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Asignar un árbitro a un partido"""
    # Verificar que el árbitro existe
    referee = await get_referee_by_id(referee_id)
    if not referee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Árbitro con ID {referee_id} no encontrado",
        )
    
    # Validar rol
    valid_roles = ["main", "assistant", "line_judge", "video_referee"]
    if role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol inválido. Debe ser uno de: {', '.join(valid_roles)}",
        )
    
    return await assign_referee_to_match(referee_id, match_id, role, confirmed, notes)


@router.get("/matches/{match_id}/referees")
async def get_match_referees(
    match_id: MatchId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener todos los árbitros asignados a un partido"""
    referees = await get_referees_for_match(match_id)
    return [
        {
            "referee": referee,
            "assignment": assignment,
        }
        for referee, assignment in referees
    ]


@router.put("/matches/{match_id}/referees/{referee_id}")
async def update_referee_match_assignment(
    match_id: MatchId,
    referee_id: RefereeId,
    confirmed: bool | None = Query(None, description="Actualizar confirmación"),
    notes: str | None = Query(None, description="Actualizar notas"),
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Actualizar la asignación de un árbitro a un partido"""
    updated = await update_referee_assignment(referee_id, match_id, confirmed, notes)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asignación no encontrada para árbitro {referee_id} en partido {match_id}",
        )
    return updated


@router.delete("/matches/{match_id}/referees/{referee_id}")
async def remove_referee_from_match_endpoint(
    match_id: MatchId,
    referee_id: RefereeId,
    _: UserPublic = Depends(user_authenticated_for_tournament),
) -> SuccessResponse:
    """Remover un árbitro de un partido"""
    removed = await remove_referee_from_match(referee_id, match_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asignación no encontrada para árbitro {referee_id} en partido {match_id}",
        )
    return SuccessResponse()


# Endpoint para obtener conflictos de horario de un árbitro
@router.get("/referees/{referee_id}/conflicts")
async def get_referee_schedule_conflicts(
    referee_id: RefereeId,
    tournament_id: TournamentId,
    date: datetime_utc | None = Query(None, description="Fecha específica para verificar conflictos"),
    _: UserPublic = Depends(user_authenticated_for_tournament),
):
    """Obtener conflictos de horario para un árbitro en un torneo"""
    # Esta función puede ser expandida para detectar conflictos complejos
    # Por ahora, retorna los partidos asignados del árbitro
    
    # TODO: Implementar lógica de detección de conflictos
    return {
        "referee_id": referee_id,
        "tournament_id": tournament_id,
        "date": date,
        "conflicts": [],
        "message": "Función de detección de conflictos pendiente de implementación completa"
    }
