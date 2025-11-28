"""GDPR Compliance Module.

Implements GDPR requirements for data handling in the European AOR.
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class LawfulBasis(str, Enum):
    """GDPR lawful basis for processing."""
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class DataCategory(str, Enum):
    """Categories of personal data."""
    BASIC_IDENTITY = "basic_identity"  # Name, email, phone
    LOCATION = "location"  # GPS, region
    BEHAVIORAL = "behavioral"  # Check-ins, app usage
    SENSITIVE = "sensitive"  # Health, religious beliefs
    BIOMETRIC = "biometric"  # Fingerprints, face data


class RequestType(str, Enum):
    """Types of data subject requests."""
    ACCESS = "access"  # Right to access
    RECTIFICATION = "rectification"  # Right to rectification
    ERASURE = "erasure"  # Right to erasure (right to be forgotten)
    RESTRICTION = "restriction"  # Right to restriction
    PORTABILITY = "portability"  # Right to data portability
    OBJECTION = "objection"  # Right to object


@dataclass
class ConsentRecord:
    """Record of user consent."""
    id: str
    user_id: str
    purpose: str
    lawful_basis: LawfulBasis
    data_categories: list[DataCategory]
    granted_at: datetime
    expires_at: Optional[datetime]
    withdrawn_at: Optional[datetime] = None
    version: str = "1.0"
    metadata: dict = field(default_factory=dict)


@dataclass
class DataSubjectRequest:
    """GDPR data subject request."""
    id: str
    user_id: str
    request_type: RequestType
    submitted_at: datetime
    status: str  # pending, processing, completed, rejected
    completed_at: Optional[datetime] = None
    response: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ProcessingActivity:
    """Record of data processing activity."""
    id: str
    name: str
    purpose: str
    lawful_basis: LawfulBasis
    data_categories: list[DataCategory]
    recipients: list[str]
    retention_period: str
    security_measures: list[str]
    created_at: datetime
    updated_at: datetime


class GDPRCompliance:
    """GDPR compliance manager.
    
    Handles:
    - Consent management
    - Data subject requests
    - Data retention policies
    - Processing activity records
    - Privacy impact assessments
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or os.getenv(
            "GDPR_STORAGE_PATH",
            "/tmp/goodshepherd/gdpr"
        ))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Default retention periods (in days)
        self.retention_periods = {
            DataCategory.BASIC_IDENTITY: 365 * 3,  # 3 years
            DataCategory.LOCATION: 90,  # 90 days
            DataCategory.BEHAVIORAL: 365,  # 1 year
            DataCategory.SENSITIVE: 365,  # 1 year
            DataCategory.BIOMETRIC: 30,  # 30 days
        }

    # =========================================================================
    # Consent Management
    # =========================================================================

    def record_consent(
        self,
        user_id: str,
        purpose: str,
        lawful_basis: LawfulBasis,
        data_categories: list[DataCategory],
        expires_in_days: Optional[int] = 365,
    ) -> ConsentRecord:
        """Record user consent for data processing."""
        consent = ConsentRecord(
            id=str(uuid4()),
            user_id=user_id,
            purpose=purpose,
            lawful_basis=lawful_basis,
            data_categories=data_categories,
            granted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None,
        )
        
        self._save_consent(consent)
        logger.info(f"Consent recorded: user={user_id}, purpose={purpose}")
        
        return consent

    def withdraw_consent(self, consent_id: str, user_id: str) -> bool:
        """Withdraw previously granted consent."""
        consent = self._load_consent(consent_id)
        if not consent or consent.user_id != user_id:
            return False
        
        consent.withdrawn_at = datetime.utcnow()
        self._save_consent(consent)
        
        logger.info(f"Consent withdrawn: id={consent_id}, user={user_id}")
        return True

    def check_consent(
        self,
        user_id: str,
        purpose: str,
        data_category: DataCategory,
    ) -> bool:
        """Check if user has valid consent for processing."""
        consents = self._load_user_consents(user_id)
        
        for consent in consents:
            if (consent.purpose == purpose and
                data_category in consent.data_categories and
                consent.withdrawn_at is None and
                (consent.expires_at is None or consent.expires_at > datetime.utcnow())):
                return True
        
        return False

    def get_user_consents(self, user_id: str) -> list[ConsentRecord]:
        """Get all consent records for a user."""
        return self._load_user_consents(user_id)

    # =========================================================================
    # Data Subject Requests
    # =========================================================================

    def submit_request(
        self,
        user_id: str,
        request_type: RequestType,
        metadata: Optional[dict] = None,
    ) -> DataSubjectRequest:
        """Submit a data subject request."""
        request = DataSubjectRequest(
            id=str(uuid4()),
            user_id=user_id,
            request_type=request_type,
            submitted_at=datetime.utcnow(),
            status="pending",
            metadata=metadata or {},
        )
        
        self._save_request(request)
        logger.info(f"DSR submitted: type={request_type}, user={user_id}")
        
        return request

    def process_access_request(self, request_id: str) -> dict:
        """Process a data access request (Article 15)."""
        request = self._load_request(request_id)
        if not request or request.request_type != RequestType.ACCESS:
            return {"error": "Invalid request"}
        
        # Collect all user data
        user_data = self._collect_user_data(request.user_id)
        
        # Update request status
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        request.response = "Data export generated"
        self._save_request(request)
        
        return {
            "request_id": request_id,
            "user_id": request.user_id,
            "data": user_data,
            "exported_at": datetime.utcnow().isoformat(),
        }

    def process_erasure_request(self, request_id: str) -> dict:
        """Process a data erasure request (Article 17)."""
        request = self._load_request(request_id)
        if not request or request.request_type != RequestType.ERASURE:
            return {"error": "Invalid request"}
        
        # Perform data erasure
        erased_items = self._erase_user_data(request.user_id)
        
        # Update request status
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        request.response = f"Erased {erased_items} data items"
        self._save_request(request)
        
        logger.info(f"Data erased for user {request.user_id}: {erased_items} items")
        
        return {
            "request_id": request_id,
            "user_id": request.user_id,
            "items_erased": erased_items,
            "completed_at": request.completed_at.isoformat(),
        }

    def process_portability_request(self, request_id: str) -> dict:
        """Process a data portability request (Article 20)."""
        request = self._load_request(request_id)
        if not request or request.request_type != RequestType.PORTABILITY:
            return {"error": "Invalid request"}
        
        # Export data in machine-readable format
        user_data = self._collect_user_data(request.user_id)
        
        # Update request status
        request.status = "completed"
        request.completed_at = datetime.utcnow()
        request.response = "Portable data export generated"
        self._save_request(request)
        
        return {
            "request_id": request_id,
            "user_id": request.user_id,
            "format": "json",
            "data": user_data,
            "exported_at": datetime.utcnow().isoformat(),
        }

    def get_request_status(self, request_id: str) -> Optional[DataSubjectRequest]:
        """Get status of a data subject request."""
        return self._load_request(request_id)

    # =========================================================================
    # Data Retention
    # =========================================================================

    def apply_retention_policy(self, data_category: DataCategory) -> int:
        """Apply retention policy and delete expired data."""
        retention_days = self.retention_periods.get(data_category, 365)
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # This would delete data older than cutoff_date
        # Implementation depends on data storage
        deleted_count = 0
        
        logger.info(
            f"Retention policy applied: category={data_category}, "
            f"cutoff={cutoff_date}, deleted={deleted_count}"
        )
        
        return deleted_count

    def get_retention_period(self, data_category: DataCategory) -> int:
        """Get retention period in days for a data category."""
        return self.retention_periods.get(data_category, 365)

    def set_retention_period(self, data_category: DataCategory, days: int):
        """Set retention period for a data category."""
        self.retention_periods[data_category] = days

    # =========================================================================
    # Processing Activity Records (Article 30)
    # =========================================================================

    def register_processing_activity(
        self,
        name: str,
        purpose: str,
        lawful_basis: LawfulBasis,
        data_categories: list[DataCategory],
        recipients: list[str],
        retention_period: str,
        security_measures: list[str],
    ) -> ProcessingActivity:
        """Register a data processing activity."""
        activity = ProcessingActivity(
            id=str(uuid4()),
            name=name,
            purpose=purpose,
            lawful_basis=lawful_basis,
            data_categories=data_categories,
            recipients=recipients,
            retention_period=retention_period,
            security_measures=security_measures,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        self._save_processing_activity(activity)
        return activity

    def get_processing_activities(self) -> list[ProcessingActivity]:
        """Get all registered processing activities."""
        return self._load_all_processing_activities()

    # =========================================================================
    # Privacy Helpers
    # =========================================================================

    def pseudonymize_id(self, user_id: str, salt: Optional[str] = None) -> str:
        """Pseudonymize a user ID."""
        salt = salt or os.getenv("GDPR_PSEUDONYM_SALT", "goodshepherd")
        return hashlib.sha256(f"{user_id}{salt}".encode()).hexdigest()[:16]

    def generate_privacy_report(self, user_id: str) -> dict:
        """Generate a privacy report for a user."""
        consents = self.get_user_consents(user_id)
        
        return {
            "user_id": self.pseudonymize_id(user_id),
            "generated_at": datetime.utcnow().isoformat(),
            "consents": [
                {
                    "purpose": c.purpose,
                    "granted_at": c.granted_at.isoformat(),
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                    "active": c.withdrawn_at is None,
                }
                for c in consents
            ],
            "data_categories_processed": list(set(
                cat for c in consents for cat in c.data_categories
            )),
            "retention_info": {
                cat.value: f"{self.retention_periods.get(cat, 365)} days"
                for cat in DataCategory
            },
        }

    # =========================================================================
    # Storage Helpers
    # =========================================================================

    def _save_consent(self, consent: ConsentRecord):
        """Save consent record to storage."""
        file_path = self.storage_path / "consents" / f"{consent.id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w") as f:
            json.dump({
                "id": consent.id,
                "user_id": consent.user_id,
                "purpose": consent.purpose,
                "lawful_basis": consent.lawful_basis.value,
                "data_categories": [c.value for c in consent.data_categories],
                "granted_at": consent.granted_at.isoformat(),
                "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                "withdrawn_at": consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                "version": consent.version,
                "metadata": consent.metadata,
            }, f)

    def _load_consent(self, consent_id: str) -> Optional[ConsentRecord]:
        """Load consent record from storage."""
        file_path = self.storage_path / "consents" / f"{consent_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path) as f:
            data = json.load(f)
        
        return ConsentRecord(
            id=data["id"],
            user_id=data["user_id"],
            purpose=data["purpose"],
            lawful_basis=LawfulBasis(data["lawful_basis"]),
            data_categories=[DataCategory(c) for c in data["data_categories"]],
            granted_at=datetime.fromisoformat(data["granted_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            withdrawn_at=datetime.fromisoformat(data["withdrawn_at"]) if data["withdrawn_at"] else None,
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {}),
        )

    def _load_user_consents(self, user_id: str) -> list[ConsentRecord]:
        """Load all consent records for a user."""
        consents_dir = self.storage_path / "consents"
        if not consents_dir.exists():
            return []
        
        consents = []
        for file_path in consents_dir.glob("*.json"):
            consent = self._load_consent(file_path.stem)
            if consent and consent.user_id == user_id:
                consents.append(consent)
        
        return consents

    def _save_request(self, request: DataSubjectRequest):
        """Save data subject request to storage."""
        file_path = self.storage_path / "requests" / f"{request.id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w") as f:
            json.dump({
                "id": request.id,
                "user_id": request.user_id,
                "request_type": request.request_type.value,
                "submitted_at": request.submitted_at.isoformat(),
                "status": request.status,
                "completed_at": request.completed_at.isoformat() if request.completed_at else None,
                "response": request.response,
                "metadata": request.metadata,
            }, f)

    def _load_request(self, request_id: str) -> Optional[DataSubjectRequest]:
        """Load data subject request from storage."""
        file_path = self.storage_path / "requests" / f"{request_id}.json"
        if not file_path.exists():
            return None
        
        with open(file_path) as f:
            data = json.load(f)
        
        return DataSubjectRequest(
            id=data["id"],
            user_id=data["user_id"],
            request_type=RequestType(data["request_type"]),
            submitted_at=datetime.fromisoformat(data["submitted_at"]),
            status=data["status"],
            completed_at=datetime.fromisoformat(data["completed_at"]) if data["completed_at"] else None,
            response=data["response"],
            metadata=data.get("metadata", {}),
        )

    def _save_processing_activity(self, activity: ProcessingActivity):
        """Save processing activity record."""
        file_path = self.storage_path / "activities" / f"{activity.id}.json"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "w") as f:
            json.dump({
                "id": activity.id,
                "name": activity.name,
                "purpose": activity.purpose,
                "lawful_basis": activity.lawful_basis.value,
                "data_categories": [c.value for c in activity.data_categories],
                "recipients": activity.recipients,
                "retention_period": activity.retention_period,
                "security_measures": activity.security_measures,
                "created_at": activity.created_at.isoformat(),
                "updated_at": activity.updated_at.isoformat(),
            }, f)

    def _load_all_processing_activities(self) -> list[ProcessingActivity]:
        """Load all processing activity records."""
        activities_dir = self.storage_path / "activities"
        if not activities_dir.exists():
            return []
        
        activities = []
        for file_path in activities_dir.glob("*.json"):
            with open(file_path) as f:
                data = json.load(f)
            
            activities.append(ProcessingActivity(
                id=data["id"],
                name=data["name"],
                purpose=data["purpose"],
                lawful_basis=LawfulBasis(data["lawful_basis"]),
                data_categories=[DataCategory(c) for c in data["data_categories"]],
                recipients=data["recipients"],
                retention_period=data["retention_period"],
                security_measures=data["security_measures"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"]),
            ))
        
        return activities

    def _collect_user_data(self, user_id: str) -> dict:
        """Collect all data for a user (for access/portability requests)."""
        # This would collect data from all systems
        # Implementation depends on data storage architecture
        return {
            "user_id": user_id,
            "consents": [
                {
                    "purpose": c.purpose,
                    "granted_at": c.granted_at.isoformat(),
                }
                for c in self.get_user_consents(user_id)
            ],
            # Additional data would be collected from other systems
        }

    def _erase_user_data(self, user_id: str) -> int:
        """Erase all data for a user."""
        erased = 0
        
        # Erase consents
        for consent in self._load_user_consents(user_id):
            file_path = self.storage_path / "consents" / f"{consent.id}.json"
            if file_path.exists():
                file_path.unlink()
                erased += 1
        
        # Additional erasure from other systems would go here
        
        return erased
