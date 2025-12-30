"""
World Situational Awareness data model extensions.

Revision ID: 006_world_awareness_models
Revises: 005_add_organization_settings
Create Date: 2025-12-29

This migration adds:
- Source model extensions (trust_baseline, source_type, collection_method)
- Region table for geographic state tracking
- RawObservation table for collection buffering
- Incident extensions (status, severity, admin override)
- IncidentEvidence table for provenance tracking
- Indicator table for slow-moving trends
- Report table for SITREP generation
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '006_world_awareness_models'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create source_type enum
    source_type_enum = postgresql.ENUM(
        'official', 'news', 'social', 'ngo', 'partner',
        name='sourcetype',
        create_type=False
    )
    source_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create collection_method enum
    collection_method_enum = postgresql.ENUM(
        'api', 'rss', 'headless',
        name='collectionmethod',
        create_type=False
    )
    collection_method_enum.create(op.get_bind(), checkfirst=True)
    
    # Create content_type enum
    content_type_enum = postgresql.ENUM(
        'text', 'image', 'video', 'dataset',
        name='contenttype',
        create_type=False
    )
    content_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create evidence_type enum
    evidence_type_enum = postgresql.ENUM(
        'text', 'image', 'video', 'dataset',
        name='evidencetype',
        create_type=False
    )
    evidence_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create incident_status enum
    incident_status_enum = postgresql.ENUM(
        'unverified', 'developing', 'corroborated', 'confirmed', 'debunked',
        name='incidentstatus',
        create_type=False
    )
    incident_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create incident_severity enum
    incident_severity_enum = postgresql.ENUM(
        'low', 'medium', 'high', 'critical',
        name='incidentseverity',
        create_type=False
    )
    incident_severity_enum.create(op.get_bind(), checkfirst=True)
    
    # Create region_status enum
    region_status_enum = postgresql.ENUM(
        'green', 'yellow', 'red',
        name='regionstatus',
        create_type=False
    )
    region_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create region_type enum
    region_type_enum = postgresql.ENUM(
        'global', 'continent', 'country', 'admin1', 'admin2', 'city', 'custom',
        name='regiontype',
        create_type=False
    )
    region_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create indicator_domain enum
    indicator_domain_enum = postgresql.ENUM(
        'geopolitical', 'migration', 'security', 'economic', 'infrastructure', 'health', 'environmental',
        name='indicatordomain',
        create_type=False
    )
    indicator_domain_enum.create(op.get_bind(), checkfirst=True)
    
    # Create report_type enum
    report_type_enum = postgresql.ENUM(
        'daily', 'weekly', 'ad_hoc',
        name='reporttype',
        create_type=False
    )
    report_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create report_status enum
    report_status_enum = postgresql.ENUM(
        'draft', 'pending', 'published', 'archived',
        name='reportstatus',
        create_type=False
    )
    report_status_enum.create(op.get_bind(), checkfirst=True)
    
    # ============================================
    # REGIONS TABLE (must be created before events due to FK)
    # ============================================
    op.create_table(
        'regions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('iso_code', sa.String(10), nullable=True, index=True),
        sa.Column('region_type', sa.Enum('global', 'continent', 'country', 'admin1', 'admin2', 'city', 'custom', name='regiontype'), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('geom', sa.Text, nullable=True),  # Will be Geometry in production with PostGIS
        sa.Column('center_lat', sa.Float, nullable=True),
        sa.Column('center_lon', sa.Float, nullable=True),
        sa.Column('status', sa.Enum('green', 'yellow', 'red', name='regionstatus'), nullable=False, default='green'),
        sa.Column('status_reason', sa.Text, nullable=True),
        sa.Column('status_updated_at', sa.DateTime, nullable=True),
        sa.Column('physical_state_score', sa.Float, nullable=True),
        sa.Column('migration_pressure_score', sa.Float, nullable=True),
        sa.Column('security_stability_score', sa.Float, nullable=True),
        sa.Column('socioeconomic_stress_score', sa.Float, nullable=True),
        sa.Column('information_reliability_score', sa.Float, nullable=True),
        sa.Column('population', sa.Integer, nullable=True),
        sa.Column('area_sq_km', sa.Float, nullable=True),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # ============================================
    # EXTEND SOURCES TABLE
    # ============================================
    # Add new columns to sources
    op.add_column('sources', sa.Column('trust_baseline', sa.Integer, nullable=True, default=50))
    op.add_column('sources', sa.Column('allowed_collection_method', sa.Enum('api', 'rss', 'headless', name='collectionmethod'), nullable=True))
    op.add_column('sources', sa.Column('url_patterns', postgresql.JSON, nullable=True))
    op.add_column('sources', sa.Column('region_focus', postgresql.JSON, nullable=True))
    
    # Set defaults for existing rows
    op.execute("UPDATE sources SET trust_baseline = 50 WHERE trust_baseline IS NULL")
    op.execute("UPDATE sources SET allowed_collection_method = 'rss' WHERE allowed_collection_method IS NULL")
    
    # Alter to not null after setting defaults
    op.alter_column('sources', 'trust_baseline', nullable=False, server_default='50')
    
    # ============================================
    # RAW_OBSERVATIONS TABLE
    # ============================================
    op.create_table(
        'raw_observations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('collected_at', sa.DateTime, nullable=False, index=True),
        sa.Column('content_type', sa.Enum('text', 'image', 'video', 'dataset', name='contenttype'), nullable=False),
        sa.Column('raw_text', sa.Text, nullable=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('media_refs', postgresql.JSON, nullable=True),
        sa.Column('original_url', sa.String(2000), nullable=True, index=True),
        sa.Column('content_hash', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('processed', sa.Boolean, nullable=False, default=False, index=True),
        sa.Column('processed_at', sa.DateTime, nullable=True),
        sa.Column('processing_error', sa.Text, nullable=True),
        sa.Column('extracted_locations', postgresql.JSON, nullable=True),
        sa.Column('extracted_timestamp', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # ============================================
    # EXTEND EVENTS TABLE (Incidents)
    # ============================================
    op.add_column('events', sa.Column('title', sa.String(300), nullable=True, index=True))
    op.add_column('events', sa.Column('occurred_at', sa.DateTime, nullable=True, index=True))
    op.add_column('events', sa.Column('description', sa.Text, nullable=True))
    op.add_column('events', sa.Column('region_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regions.id', ondelete='SET NULL'), nullable=True, index=True))
    op.add_column('events', sa.Column('status', sa.Enum('unverified', 'developing', 'corroborated', 'confirmed', 'debunked', name='incidentstatus'), nullable=True))
    op.add_column('events', sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='incidentseverity'), nullable=True))
    op.add_column('events', sa.Column('tags', postgresql.JSON, nullable=True))
    op.add_column('events', sa.Column('admin_override_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
    op.add_column('events', sa.Column('admin_override_at', sa.DateTime, nullable=True))
    op.add_column('events', sa.Column('admin_notes', sa.Text, nullable=True))
    op.add_column('events', sa.Column('pinned_to_reports', postgresql.JSON, nullable=True))
    
    # Set defaults for existing events
    op.execute("UPDATE events SET status = 'confirmed' WHERE status IS NULL")
    op.execute("UPDATE events SET severity = 'medium' WHERE severity IS NULL")
    
    # Alter to not null
    op.alter_column('events', 'status', nullable=False, server_default='unverified')
    op.alter_column('events', 'severity', nullable=False, server_default='medium')
    
    # Create index on status
    op.create_index('ix_events_status', 'events', ['status'])
    
    # ============================================
    # INCIDENT_EVIDENCE TABLE
    # ============================================
    op.create_table(
        'incident_evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('events.event_id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('observation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('raw_observations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('evidence_type', sa.Enum('text', 'image', 'video', 'dataset', name='evidencetype'), nullable=False),
        sa.Column('excerpt', sa.Text, nullable=True),
        sa.Column('weight', sa.Float, nullable=False, default=1.0),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verification_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # ============================================
    # INDICATORS TABLE
    # ============================================
    op.create_table(
        'indicators',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('region_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('regions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('domain', sa.Enum('geopolitical', 'migration', 'security', 'economic', 'infrastructure', 'health', 'environmental', name='indicatordomain'), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('value', sa.Float, nullable=False, default=50.0),
        sa.Column('delta_24h', sa.Float, nullable=True),
        sa.Column('delta_7d', sa.Float, nullable=True),
        sa.Column('confidence', sa.Float, nullable=False, default=50.0),
        sa.Column('evidence_links', postgresql.JSON, nullable=True),
        sa.Column('historical_values', postgresql.JSON, nullable=True),
        sa.Column('measured_at', sa.DateTime, nullable=False, index=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # ============================================
    # REPORTS TABLE
    # ============================================
    op.create_table(
        'reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_type', sa.Enum('daily', 'weekly', 'ad_hoc', name='reporttype'), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('region_scope', postgresql.JSON, nullable=True),
        sa.Column('period_start', sa.DateTime, nullable=True),
        sa.Column('period_end', sa.DateTime, nullable=True),
        sa.Column('status', sa.Enum('draft', 'pending', 'published', 'archived', name='reportstatus'), nullable=False, default='draft'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('executive_summary', sa.Text, nullable=True),
        sa.Column('narrative_markdown', sa.Text, nullable=True),
        sa.Column('key_developments', postgresql.JSON, nullable=True),
        sa.Column('areas_to_watch', postgresql.JSON, nullable=True),
        sa.Column('forward_outlook', sa.Text, nullable=True),
        sa.Column('included_incident_ids', postgresql.JSON, nullable=True),
        sa.Column('included_indicator_ids', postgresql.JSON, nullable=True),
        sa.Column('map_snapshot_url', sa.String(500), nullable=True),
        sa.Column('chart_urls', postgresql.JSON, nullable=True),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('docx_url', sa.String(500), nullable=True),
        sa.Column('confidence_notes', sa.Text, nullable=True),
        sa.Column('distribution_list', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.Column('published_at', sa.DateTime, nullable=True),
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('reports')
    op.drop_table('indicators')
    op.drop_table('incident_evidence')
    op.drop_table('raw_observations')
    op.drop_table('regions')
    
    # Remove event extensions
    op.drop_index('ix_events_status', 'events')
    op.drop_column('events', 'pinned_to_reports')
    op.drop_column('events', 'admin_notes')
    op.drop_column('events', 'admin_override_at')
    op.drop_column('events', 'admin_override_by')
    op.drop_column('events', 'tags')
    op.drop_column('events', 'severity')
    op.drop_column('events', 'status')
    op.drop_column('events', 'region_id')
    op.drop_column('events', 'description')
    op.drop_column('events', 'occurred_at')
    op.drop_column('events', 'title')
    
    # Remove source extensions
    op.drop_column('sources', 'region_focus')
    op.drop_column('sources', 'url_patterns')
    op.drop_column('sources', 'allowed_collection_method')
    op.drop_column('sources', 'trust_baseline')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS reportstatus")
    op.execute("DROP TYPE IF EXISTS reporttype")
    op.execute("DROP TYPE IF EXISTS indicatordomain")
    op.execute("DROP TYPE IF EXISTS regiontype")
    op.execute("DROP TYPE IF EXISTS regionstatus")
    op.execute("DROP TYPE IF EXISTS incidentseverity")
    op.execute("DROP TYPE IF EXISTS incidentstatus")
    op.execute("DROP TYPE IF EXISTS evidencetype")
    op.execute("DROP TYPE IF EXISTS contenttype")
    op.execute("DROP TYPE IF EXISTS collectionmethod")
    op.execute("DROP TYPE IF EXISTS sourcetype")
