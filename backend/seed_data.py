"""
Seed data for World Situational Awareness platform.
Includes sample regions, sources, and a LATAM strategic risk indicator.
"""
from datetime import datetime, timedelta
from uuid import uuid4
import json

from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.source import Source, SourceType, CollectionMethod
from backend.models.region import Region, RegionStatus, RegionType
from backend.models.indicator import Indicator, IndicatorDomain
from backend.models.event import Event, EventCategory, IncidentStatus, IncidentSeverity


def create_seed_regions(db: Session) -> dict:
    """Create seed regions for the platform."""
    regions = {}
    
    # Global region
    global_region = Region(
        id=uuid4(),
        name="Global",
        region_type=RegionType.GLOBAL,
        status=RegionStatus.GREEN,
        physical_state_score=25.0,
        migration_pressure_score=40.0,
        security_stability_score=35.0,
        socioeconomic_stress_score=45.0,
        information_reliability_score=70.0
    )
    db.add(global_region)
    regions["global"] = global_region
    
    # Latin America (LATAM) - elevated concern
    latam = Region(
        id=uuid4(),
        name="Latin America",
        iso_code="LATAM",
        region_type=RegionType.CONTINENT,
        parent_id=global_region.id,
        status=RegionStatus.YELLOW,
        status_reason="Elevated migration pressure and security concerns",
        status_updated_at=datetime.utcnow(),
        center_lat=4.5,
        center_lon=-73.0,
        physical_state_score=40.0,
        migration_pressure_score=72.0,
        security_stability_score=55.0,
        socioeconomic_stress_score=60.0,
        information_reliability_score=55.0,
        population=650000000,
        summary="Region experiencing elevated migration flows and security challenges"
    )
    db.add(latam)
    regions["latam"] = latam
    
    # Venezuela - critical
    venezuela = Region(
        id=uuid4(),
        name="Venezuela",
        iso_code="VE",
        region_type=RegionType.COUNTRY,
        parent_id=latam.id,
        status=RegionStatus.RED,
        status_reason="Critical humanitarian and political situation",
        status_updated_at=datetime.utcnow(),
        center_lat=6.4238,
        center_lon=-66.5897,
        physical_state_score=75.0,
        migration_pressure_score=90.0,
        security_stability_score=80.0,
        socioeconomic_stress_score=85.0,
        information_reliability_score=40.0,
        population=28500000
    )
    db.add(venezuela)
    regions["venezuela"] = venezuela
    
    # Colombia
    colombia = Region(
        id=uuid4(),
        name="Colombia",
        iso_code="CO",
        region_type=RegionType.COUNTRY,
        parent_id=latam.id,
        status=RegionStatus.YELLOW,
        status_reason="Receiving significant migrant flows from Venezuela",
        status_updated_at=datetime.utcnow(),
        center_lat=4.5709,
        center_lon=-74.2973,
        physical_state_score=35.0,
        migration_pressure_score=65.0,
        security_stability_score=50.0,
        socioeconomic_stress_score=45.0,
        information_reliability_score=65.0,
        population=51000000
    )
    db.add(colombia)
    regions["colombia"] = colombia
    
    # Europe - for original use case
    europe = Region(
        id=uuid4(),
        name="Europe",
        iso_code="EU",
        region_type=RegionType.CONTINENT,
        parent_id=global_region.id,
        status=RegionStatus.GREEN,
        center_lat=51.1657,
        center_lon=10.4515,
        physical_state_score=20.0,
        migration_pressure_score=45.0,
        security_stability_score=25.0,
        socioeconomic_stress_score=35.0,
        information_reliability_score=85.0,
        population=450000000
    )
    db.add(europe)
    regions["europe"] = europe
    
    return regions


def create_seed_sources(db: Session) -> dict:
    """Create seed data sources."""
    sources = {}
    
    # Official sources - high trust
    sources["gdacs"] = Source(
        name="GDACS - Global Disaster Alert",
        source_type=SourceType.OFFICIAL,
        url="https://www.gdacs.org/rss.aspx",
        trust_baseline=85,
        allowed_collection_method=CollectionMethod.RSS,
        description="Global Disaster Alert and Coordination System",
        is_active=True
    )
    db.add(sources["gdacs"])
    
    sources["reliefweb"] = Source(
        name="ReliefWeb",
        source_type=SourceType.OFFICIAL,
        url="https://api.reliefweb.int/v1/reports",
        trust_baseline=80,
        allowed_collection_method=CollectionMethod.API,
        description="UN OCHA humanitarian information",
        is_active=True
    )
    db.add(sources["reliefweb"])
    
    # NGO sources - medium-high trust
    sources["unhcr"] = Source(
        name="UNHCR News",
        source_type=SourceType.NGO,
        url="https://www.unhcr.org/rss/news.xml",
        trust_baseline=75,
        allowed_collection_method=CollectionMethod.RSS,
        description="UN Refugee Agency updates",
        is_active=True
    )
    db.add(sources["unhcr"])
    
    # News sources - medium trust
    sources["reuters"] = Source(
        name="Reuters World News",
        source_type=SourceType.NEWS,
        url="https://www.reutersagency.com/feed/",
        trust_baseline=70,
        allowed_collection_method=CollectionMethod.RSS,
        description="Reuters international news feed",
        is_active=True
    )
    db.add(sources["reuters"])
    
    sources["bbc"] = Source(
        name="BBC World",
        source_type=SourceType.NEWS,
        url="http://feeds.bbci.co.uk/news/world/rss.xml",
        trust_baseline=72,
        allowed_collection_method=CollectionMethod.RSS,
        description="BBC World news feed",
        is_active=True
    )
    db.add(sources["bbc"])
    
    return sources


def create_latam_indicators(db: Session, regions: dict) -> list:
    """Create LATAM strategic risk indicators."""
    indicators = []
    
    # Venezuela migration pressure indicator
    ve_migration = Indicator(
        region_id=regions["venezuela"].id,
        name="Migration Pressure Index",
        domain=IndicatorDomain.MIGRATION,
        description="Composite index of outbound migration pressure",
        value=90.0,
        delta_24h=0.5,
        delta_7d=3.2,
        confidence=75.0,
        measured_at=datetime.utcnow(),
        historical_values=[
            {"timestamp": (datetime.utcnow() - timedelta(days=7)).isoformat(), "value": 86.8},
            {"timestamp": (datetime.utcnow() - timedelta(days=6)).isoformat(), "value": 87.2},
            {"timestamp": (datetime.utcnow() - timedelta(days=5)).isoformat(), "value": 87.8},
            {"timestamp": (datetime.utcnow() - timedelta(days=4)).isoformat(), "value": 88.1},
            {"timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat(), "value": 88.5},
            {"timestamp": (datetime.utcnow() - timedelta(days=2)).isoformat(), "value": 89.0},
            {"timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(), "value": 89.5},
        ]
    )
    db.add(ve_migration)
    indicators.append(ve_migration)
    
    # Venezuela security indicator
    ve_security = Indicator(
        region_id=regions["venezuela"].id,
        name="Security Stability Index",
        domain=IndicatorDomain.SECURITY,
        description="Composite index of internal security conditions",
        value=80.0,
        delta_24h=-0.2,
        delta_7d=1.5,
        confidence=60.0,
        measured_at=datetime.utcnow()
    )
    db.add(ve_security)
    indicators.append(ve_security)
    
    # Colombia migration receiving indicator
    co_migration = Indicator(
        region_id=regions["colombia"].id,
        name="Migration Inflow Index",
        domain=IndicatorDomain.MIGRATION,
        description="Index of incoming migration from neighboring countries",
        value=65.0,
        delta_24h=0.3,
        delta_7d=2.1,
        confidence=70.0,
        measured_at=datetime.utcnow()
    )
    db.add(co_migration)
    indicators.append(co_migration)
    
    # LATAM overall indicator
    latam_stability = Indicator(
        region_id=regions["latam"].id,
        name="Regional Stability Index",
        domain=IndicatorDomain.GEOPOLITICAL,
        description="Aggregate stability indicator for Latin America",
        value=55.0,
        delta_24h=0.1,
        delta_7d=-0.5,
        confidence=65.0,
        measured_at=datetime.utcnow()
    )
    db.add(latam_stability)
    indicators.append(latam_stability)
    
    return indicators


def create_sample_incidents(db: Session, regions: dict) -> list:
    """Create sample incidents for demonstration."""
    incidents = []
    
    # Venezuela border crossing incident
    ve_border = Event(
        title="Increased Migration Flow at Colombian Border",
        timestamp=datetime.utcnow() - timedelta(hours=6),
        occurred_at=datetime.utcnow() - timedelta(hours=12),
        summary="Reports indicate increased migration flow through unofficial border crossings between Venezuela and Colombia.",
        full_text="Local officials report a 30% increase in migrants crossing at unofficial points along the Venezuela-Colombia border. UNHCR field teams are deploying additional support.",
        category=EventCategory.MIGRATION,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.CORROBORATED,
        confidence_score=0.72,
        relevance_score=0.85,
        location_name="Cúcuta, Colombia",
        location_lat=7.9253,
        location_lon=-72.5028,
        region_id=regions["colombia"].id,
        tags=["migration", "humanitarian"],
        source_list=[
            {"name": "UNHCR Field Report", "url": "https://unhcr.org/example", "trust": 75}
        ]
    )
    db.add(ve_border)
    incidents.append(ve_border)
    
    # Caracas power outage
    ve_power = Event(
        title="Power Outages Reported in Caracas Metro Area",
        timestamp=datetime.utcnow() - timedelta(hours=3),
        occurred_at=datetime.utcnow() - timedelta(hours=5),
        summary="Multiple districts in Caracas experiencing power outages affecting essential services.",
        category=EventCategory.INFRASTRUCTURE,
        severity=IncidentSeverity.MEDIUM,
        status=IncidentStatus.DEVELOPING,
        confidence_score=0.45,
        relevance_score=0.60,
        location_name="Caracas, Venezuela",
        location_lat=10.4806,
        location_lon=-66.9036,
        region_id=regions["venezuela"].id,
        tags=["infrastructure"]
    )
    db.add(ve_power)
    incidents.append(ve_power)
    
    # Unverified claim
    unverified = Event(
        title="Social Media Reports of Protest in Maracaibo",
        timestamp=datetime.utcnow() - timedelta(hours=1),
        summary="Unverified social media posts claim protests in Maracaibo. No official confirmation.",
        category=EventCategory.POLITICAL,
        severity=IncidentSeverity.LOW,
        status=IncidentStatus.UNVERIFIED,
        confidence_score=0.18,
        relevance_score=0.50,
        location_name="Maracaibo, Venezuela",
        location_lat=10.6544,
        location_lon=-71.6393,
        region_id=regions["venezuela"].id,
        tags=["political", "unverified_claim"]
    )
    db.add(unverified)
    incidents.append(unverified)
    
    return incidents


def run_seed():
    """Run all seed data creation."""
    db = SessionLocal()
    
    try:
        print("Creating seed regions...")
        regions = create_seed_regions(db)
        print(f"  Created {len(regions)} regions")
        
        print("Creating seed sources...")
        sources = create_seed_sources(db)
        print(f"  Created {len(sources)} sources")
        
        print("Creating LATAM strategic indicators...")
        indicators = create_latam_indicators(db, regions)
        print(f"  Created {len(indicators)} indicators")
        
        print("Creating sample incidents...")
        incidents = create_sample_incidents(db, regions)
        print(f"  Created {len(incidents)} incidents")
        
        db.commit()
        print("\n✅ Seed data created successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating seed data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
