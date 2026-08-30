from ..utils.database import db
from datetime import datetime, timezone
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    token_version = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=utc_now)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(50), nullable=True)
    guardian_name = db.Column(db.String(200), nullable=True)
    preferred_language = db.Column(db.String(50), nullable=True)
    occupation = db.Column(db.String(120), nullable=True)
    education_qualification = db.Column(db.String(150), nullable=True)
    address_line = db.Column(db.String(300), nullable=True)
    city = db.Column(db.String(120), nullable=True)
    district = db.Column(db.String(120), nullable=True)
    state = db.Column(db.String(120), nullable=True)
    postal_code = db.Column(db.String(10), nullable=True)
    alternate_phone = db.Column(db.String(50), nullable=True)
    alternate_email = db.Column(db.String(200), nullable=True)
    accessibility_needs = db.Column(db.String(500), nullable=True)
    service_notes = db.Column(db.String(1000), nullable=True)
    profile_updated_at = db.Column(db.DateTime, nullable=True)

    def service_profile_dict(self):
        return {
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'gender': self.gender,
            'guardian_name': self.guardian_name,
            'preferred_language': self.preferred_language,
            'occupation': self.occupation,
            'education_qualification': self.education_qualification,
            'address_line': self.address_line,
            'city': self.city,
            'district': self.district,
            'state': self.state,
            'postal_code': self.postal_code,
            'alternate_phone': self.alternate_phone,
            'alternate_email': self.alternate_email,
            'accessibility_needs': self.accessibility_needs,
            'service_notes': self.service_notes,
            'profile_updated_at': self.profile_updated_at.isoformat() if self.profile_updated_at else None,
        }

    def to_dict(self, include_service_profile=False):
        data = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'phone': self.phone,
            'is_admin': self.is_admin,
            'is_active': bool(self.is_active),
            'email_verified': bool(self.email_verified),
            'created_at': self.created_at.isoformat()
        }
        if include_service_profile:
            data['service_profile'] = self.service_profile_dict()
        return data
