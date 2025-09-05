"""add referees and scheduling improvements

Revision ID: add_referees_001
Revises: fa53e635f410
Create Date: 2024-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_referees_001'
down_revision: Union[str, None] = 'fa53e635f410'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla de árbitros
    op.create_table('referees',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('certification_level', sa.String(), nullable=True),
        sa.Column('created', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('active', sa.Boolean(), server_default='t', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_referees_id'), 'referees', ['id'], unique=False)

    # Crear tabla de relación árbitros x torneos (disponibilidad)
    op.create_table('referees_x_tournaments',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('referee_id', sa.BigInteger(), nullable=False),
        sa.Column('tournament_id', sa.BigInteger(), nullable=False),
        sa.Column('available_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('available_to', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_matches_per_day', sa.Integer(), server_default='5', nullable=False),
        sa.Column('preferred_courts', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['referee_id'], ['referees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referee_id', 'tournament_id', name='unique_referee_tournament')
    )
    op.create_index(op.f('ix_referees_x_tournaments_id'), 'referees_x_tournaments', ['id'], unique=False)

    # Crear tabla de relación árbitros x partidos (asignaciones)
    op.create_table('referees_x_matches',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('referee_id', sa.BigInteger(), nullable=False),
        sa.Column('match_id', sa.BigInteger(), nullable=False),
        sa.Column('role', sa.String(), server_default="'main'", nullable=False),
        sa.Column('confirmed', sa.Boolean(), server_default='f', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['referee_id'], ['referees.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('referee_id', 'match_id', 'role', name='unique_referee_match_role')
    )
    op.create_index(op.f('ix_referees_x_matches_id'), 'referees_x_matches', ['id'], unique=False)

    # Crear tabla de slots de tiempo
    op.create_table('time_slots',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('tournament_id', sa.BigInteger(), nullable=False),
        sa.Column('court_id', sa.BigInteger(), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_available', sa.Boolean(), server_default='t', nullable=False),
        sa.Column('match_id', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['tournament_id'], ['tournaments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['court_id'], ['courts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['match_id'], ['matches.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('court_id', 'start_time', 'end_time', name='unique_court_time_slot')
    )
    op.create_index(op.f('ix_time_slots_id'), 'time_slots', ['id'], unique=False)


def downgrade() -> None:
    # Eliminar tablas en orden inverso
    op.drop_index(op.f('ix_time_slots_id'), table_name='time_slots')
    op.drop_table('time_slots')
    
    op.drop_index(op.f('ix_referees_x_matches_id'), table_name='referees_x_matches')
    op.drop_table('referees_x_matches')
    
    op.drop_index(op.f('ix_referees_x_tournaments_id'), table_name='referees_x_tournaments')
    op.drop_table('referees_x_tournaments')
    
    op.drop_index(op.f('ix_referees_id'), table_name='referees')
    op.drop_table('referees')

