"""Create editor_projects and subtitle_files tables

Revision ID: 4a7b8c9d0e1f
Revises: cb9980f62ff0
Create Date: 2025-12-18 19:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '4a7b8c9d0e1f'
down_revision: Union[str, Sequence[str], None] = 'cb9980f62ff0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create editor tables."""
    # Create editor_projects table
    op.create_table(
        'editor_projects',
        sa.Column('id', sa.String(100), primary_key=True, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timeline_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('output_path', sa.String(500), nullable=True),
        sa.Column('output_format', sa.String(10), server_default='mp4'),
        sa.Column('output_quality', sa.String(20), server_default='high'),
        sa.Column('render_progress', sa.Float(), server_default='0.0'),
        sa.Column('render_error', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Create subtitle_files table
    op.create_table(
        'subtitle_files',
        sa.Column('id', sa.String(100), primary_key=True, index=True),
        sa.Column('project_id', sa.String(100), index=True, nullable=False),
        sa.Column('language', sa.String(10), server_default='zh-CN'),
        sa.Column('segments_json', sa.JSON(), nullable=False),
        sa.Column('default_font_size', sa.Integer(), server_default='40'),
        sa.Column('default_color', sa.String(20), server_default='#FFFFFF'),
        sa.Column('default_font_family', sa.String(100), server_default='Arial'),
        sa.Column('default_position', sa.String(20), server_default='bottom'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    """Drop editor tables."""
    op.drop_table('subtitle_files')
    op.drop_table('editor_projects')
