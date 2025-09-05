"""
Ejemplo de cliente Python para la API de Gestión de Torneos
Este script demuestra cómo usar los principales endpoints de la API
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class TournamentAPIClient:
    """Cliente para interactuar con la API de torneos"""
    
    def __init__(self, base_url: str, email: str, password: str):
        """
        Inicializar el cliente de la API
        
        Args:
            base_url: URL base de la API (ej: http://localhost:8000)
            email: Email del usuario
            password: Contraseña del usuario
        """
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.headers = {}
        self._authenticate(email, password)
    
    def _authenticate(self, email: str, password: str):
        """Autenticarse y obtener token de acceso"""
        response = requests.post(
            f"{self.base_url}/token",
            data={
                "username": email,
                "password": password,
                "grant_type": "password"
            }
        )
        response.raise_for_status()
        data = response.json()
        self.token = data["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        print(f"✅ Autenticado exitosamente")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Hacer una petición a la API"""
        url = f"{self.base_url}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            **kwargs
        )
        response.raise_for_status()
        return response.json() if response.text else {}
    
    # === TORNEOS ===
    
    def crear_torneo(self, nombre: str, club_id: int, fecha_inicio: datetime) -> Dict:
        """Crear un nuevo torneo"""
        data = {
            "name": nombre,
            "club_id": club_id,
            "start_time": fecha_inicio.isoformat(),
            "dashboard_public": True,
            "duration_minutes": 90,
            "margin_minutes": 15,
            "players_can_be_in_multiple_teams": False,
            "auto_assign_courts": True
        }
        result = self._request("POST", "/tournaments", json=data)
        print(f"✅ Torneo '{nombre}' creado con ID: {result.get('id')}")
        return result
    
    def listar_torneos(self, filtro: str = "OPEN") -> List[Dict]:
        """Listar torneos"""
        result = self._request("GET", f"/tournaments?filter={filtro}")
        print(f"📋 Encontrados {len(result.get('data', []))} torneos")
        return result.get('data', [])
    
    # === ÁRBITROS ===
    
    def registrar_arbitro(self, nombre: str, email: str, nivel: str = "Regional") -> Dict:
        """Registrar un nuevo árbitro en el sistema"""
        data = {
            "name": nombre,
            "email": email,
            "certification_level": nivel,
            "active": True
        }
        result = self._request("POST", "/referees", json=data)
        print(f"✅ Árbitro '{nombre}' registrado con ID: {result.get('id')}")
        return result
    
    def asignar_arbitro_a_torneo(
        self,
        tournament_id: int,
        referee_id: int,
        disponible_desde: datetime,
        disponible_hasta: datetime,
        max_partidos: int = 3
    ) -> Dict:
        """Asignar un árbitro a un torneo con su disponibilidad"""
        data = {
            "referee_id": referee_id,
            "tournament_id": tournament_id,
            "available_from": disponible_desde.isoformat(),
            "available_to": disponible_hasta.isoformat(),
            "max_matches_per_day": max_partidos
        }
        result = self._request(
            "POST",
            f"/tournaments/{tournament_id}/referees/{referee_id}",
            json=data
        )
        print(f"✅ Árbitro {referee_id} asignado al torneo {tournament_id}")
        return result
    
    def asignar_arbitro_a_partido(
        self,
        match_id: int,
        referee_id: int,
        rol: str = "main",
        confirmado: bool = False
    ) -> Dict:
        """Asignar un árbitro a un partido específico"""
        params = {
            "role": rol,
            "confirmed": confirmado
        }
        result = self._request(
            "POST",
            f"/matches/{match_id}/referees/{referee_id}",
            params=params
        )
        print(f"✅ Árbitro {referee_id} asignado al partido {match_id} como {rol}")
        return result
    
    def obtener_arbitros_disponibles(
        self,
        tournament_id: int,
        inicio: datetime,
        fin: datetime
    ) -> List[Dict]:
        """Obtener árbitros disponibles para un horario específico"""
        params = {
            "start_time": inicio.isoformat(),
            "end_time": fin.isoformat()
        }
        result = self._request(
            "GET",
            f"/tournaments/{tournament_id}/referees/available",
            params=params
        )
        print(f"👨‍⚖️ {len(result)} árbitros disponibles para el horario especificado")
        return result
    
    # === SLOTS DE TIEMPO ===
    
    def crear_slots_masivos(
        self,
        tournament_id: int,
        court_ids: List[int],
        fecha_inicio: datetime,
        fecha_fin: datetime,
        duracion_slot: int = 90,
        descanso: int = 15
    ) -> Dict:
        """Crear múltiples slots de tiempo de forma masiva"""
        data = {
            "tournament_id": tournament_id,
            "court_ids": court_ids,
            "start_date": fecha_inicio.isoformat(),
            "end_date": fecha_fin.isoformat(),
            "slot_duration_minutes": duracion_slot,
            "break_duration_minutes": descanso,
            "daily_start_time": "09:00",
            "daily_end_time": "21:00",
            "exclude_days": [6]  # Excluir domingos
        }
        result = self._request(
            "POST",
            f"/tournaments/{tournament_id}/time-slots/bulk",
            json=data
        )
        print(f"✅ {result.get('created_count', 0)} slots de tiempo creados")
        return result
    
    def obtener_slots_disponibles(
        self,
        tournament_id: int,
        fecha: Optional[datetime] = None,
        court_id: Optional[int] = None
    ) -> List[Dict]:
        """Obtener slots de tiempo disponibles"""
        params = {"only_available": True}
        if fecha:
            params["date"] = fecha.isoformat()
        if court_id:
            params["court_id"] = court_id
        
        result = self._request(
            "GET",
            f"/tournaments/{tournament_id}/time-slots",
            params=params
        )
        print(f"⏰ {len(result)} slots disponibles encontrados")
        return result
    
    def asignar_partido_a_slot(self, slot_id: int, match_id: int) -> Dict:
        """Asignar un partido a un slot de tiempo"""
        result = self._request(
            "POST",
            f"/time-slots/{slot_id}/assign-match",
            json={"match_id": match_id}
        )
        print(f"✅ Partido {match_id} asignado al slot {slot_id}")
        return result
    
    def obtener_disponibilidad_calendario(
        self,
        tournament_id: int,
        fecha: datetime
    ) -> Dict:
        """Obtener resumen de disponibilidad para una fecha"""
        params = {"date": fecha.isoformat()}
        result = self._request(
            "GET",
            f"/tournaments/{tournament_id}/schedule-availability",
            params=params
        )
        print(f"📊 Disponibilidad: {result.get('availability_percentage', 0):.1f}%")
        return result
    
    # === EQUIPOS ===
    
    def registrar_equipo(self, tournament_id: int, nombre: str) -> Dict:
        """Registrar un equipo en el torneo"""
        data = {
            "name": nombre,
            "active": True
        }
        result = self._request(
            "POST",
            f"/tournaments/{tournament_id}/teams",
            json=data
        )
        print(f"✅ Equipo '{nombre}' registrado con ID: {result.get('id')}")
        return result
    
    # === CANCHAS ===
    
    def crear_cancha(self, tournament_id: int, nombre: str) -> Dict:
        """Crear una cancha para el torneo"""
        data = {"name": nombre}
        result = self._request(
            "POST",
            f"/tournaments/{tournament_id}/courts",
            json=data
        )
        print(f"✅ Cancha '{nombre}' creada con ID: {result.get('id')}")
        return result
    
    # === PARTIDOS ===
    
    def actualizar_resultado_partido(
        self,
        tournament_id: int,
        match_id: int,
        score1: int,
        score2: int
    ) -> Dict:
        """Actualizar el resultado de un partido"""
        data = {
            "stage_item_input1_score": score1,
            "stage_item_input2_score": score2
        }
        result = self._request(
            "PUT",
            f"/tournaments/{tournament_id}/matches/{match_id}",
            json=data
        )
        print(f"✅ Resultado actualizado: {score1} - {score2}")
        return result
    
    def programar_partidos_automaticamente(self, tournament_id: int) -> Dict:
        """Programar automáticamente todos los partidos sin horario"""
        result = self._request(
            "POST",
            f"/tournaments/{tournament_id}/schedule_matches"
        )
        print(f"✅ Partidos programados automáticamente")
        return result


def ejemplo_flujo_completo():
    """
    Ejemplo de flujo completo para configurar y gestionar un torneo
    """
    print("=" * 60)
    print("🏆 EJEMPLO DE GESTIÓN DE TORNEO CON API")
    print("=" * 60)
    
    # Configuración
    API_URL = "http://localhost:8000"
    EMAIL = "admin@ejemplo.com"
    PASSWORD = "password123"
    
    # Inicializar cliente
    client = TournamentAPIClient(API_URL, EMAIL, PASSWORD)
    
    # 1. Crear un torneo
    print("\n📅 PASO 1: Crear Torneo")
    fecha_inicio = datetime.now() + timedelta(days=7)
    torneo = client.crear_torneo(
        nombre="Copa Estrella Blanca 2024",
        club_id=1,
        fecha_inicio=fecha_inicio
    )
    tournament_id = torneo["id"]
    
    # 2. Crear canchas
    print("\n🏟️ PASO 2: Crear Canchas")
    canchas = []
    for i in range(1, 4):
        cancha = client.crear_cancha(tournament_id, f"Cancha {i}")
        canchas.append(cancha["id"])
    
    # 3. Registrar árbitros
    print("\n👨‍⚖️ PASO 3: Registrar Árbitros")
    arbitros = [
        client.registrar_arbitro("Juan Pérez", "juan@ejemplo.com", "Nacional"),
        client.registrar_arbitro("María García", "maria@ejemplo.com", "Regional"),
        client.registrar_arbitro("Carlos López", "carlos@ejemplo.com", "Regional"),
    ]
    
    # 4. Asignar árbitros al torneo
    print("\n📝 PASO 4: Asignar Árbitros al Torneo")
    for arbitro in arbitros:
        client.asignar_arbitro_a_torneo(
            tournament_id=tournament_id,
            referee_id=arbitro["id"],
            disponible_desde=fecha_inicio,
            disponible_hasta=fecha_inicio + timedelta(days=3),
            max_partidos=3
        )
    
    # 5. Crear slots de tiempo
    print("\n⏰ PASO 5: Crear Slots de Tiempo")
    client.crear_slots_masivos(
        tournament_id=tournament_id,
        court_ids=canchas,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_inicio + timedelta(days=2),
        duracion_slot=90,
        descanso=15
    )
    
    # 6. Registrar equipos
    print("\n⚽ PASO 6: Registrar Equipos")
    equipos = [
        "Real Madrid",
        "Barcelona",
        "Atlético Madrid",
        "Valencia",
        "Sevilla",
        "Real Sociedad",
        "Villarreal",
        "Athletic Bilbao"
    ]
    for nombre_equipo in equipos:
        client.registrar_equipo(tournament_id, nombre_equipo)
    
    # 7. Verificar disponibilidad
    print("\n📊 PASO 7: Verificar Disponibilidad")
    client.obtener_disponibilidad_calendario(tournament_id, fecha_inicio)
    
    # 8. Obtener árbitros disponibles para un horario
    print("\n🔍 PASO 8: Buscar Árbitros Disponibles")
    hora_partido = fecha_inicio.replace(hour=10, minute=0)
    arbitros_disponibles = client.obtener_arbitros_disponibles(
        tournament_id,
        hora_partido,
        hora_partido + timedelta(hours=2)
    )
    
    print("\n✅ ¡Torneo configurado exitosamente!")
    print("=" * 60)
    
    return client, tournament_id


if __name__ == "__main__":
    # Ejecutar ejemplo
    try:
        client, tournament_id = ejemplo_flujo_completo()
        
        print("\n📌 Información adicional:")
        print(f"- ID del torneo creado: {tournament_id}")
        print(f"- URL del dashboard público: http://localhost:3000/tournaments/{tournament_id}")
        print(f"- API docs: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Asegúrate de que el servidor esté ejecutándose y las credenciales sean correctas")

