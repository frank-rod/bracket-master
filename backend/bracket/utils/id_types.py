"""ID types for the application."""

from typing import NewType

ClubId = NewType("ClubId", int)
CourtId = NewType("CourtId", int)
MatchId = NewType("MatchId", int)
PlayerId = NewType("PlayerId", int)
RankingId = NewType("RankingId", int)
RefereeId = NewType("RefereeId", int)  # Nuevo tipo para árbitros
RoundId = NewType("RoundId", int)
StageId = NewType("StageId", int)
StageItemId = NewType("StageItemId", int)
StageItemInputId = NewType("StageItemInputId", int)
TeamId = NewType("TeamId", int)
TimeSlotId = NewType("TimeSlotId", int)
TournamentId = NewType("TournamentId", int)
UserId = NewType("UserId", int)