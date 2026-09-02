from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint, UniqueConstraint

from ..utils.database import db


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class JobSource(db.Model):
    __tablename__ = 'job_sources'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(60), nullable=False, unique=True, index=True)
    name = db.Column(db.String(160), nullable=False)
    listing_url = db.Column(db.String(1000), nullable=False)
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    last_sync_started_at = db.Column(db.DateTime, nullable=True)
    last_sync_completed_at = db.Column(db.DateTime, nullable=True)
    last_sync_status = db.Column(db.String(30), nullable=False, default='not_run')
    last_error = db.Column(db.String(1000), nullable=True)
    fetched_count = db.Column(db.Integer, nullable=False, default=0)
    published_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    jobs = db.relationship('JobNotification', back_populates='source', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'name': self.name,
            'listing_url': self.listing_url,
            'enabled': bool(self.enabled),
            'last_sync_started_at': self.last_sync_started_at.isoformat() if self.last_sync_started_at else None,
            'last_sync_completed_at': self.last_sync_completed_at.isoformat() if self.last_sync_completed_at else None,
            'last_sync_status': self.last_sync_status,
            'last_error': self.last_error,
            'fetched_count': int(self.fetched_count or 0),
            'published_count': int(self.published_count or 0),
        }


class JobNotification(db.Model):
    __tablename__ = 'job_notifications'
    __table_args__ = (
        UniqueConstraint('source_id', 'external_id', name='uq_job_source_external_id'),
        CheckConstraint("status IN ('published','needs_review','expired','hidden')", name='ck_job_status'),
        CheckConstraint('confidence >= 0 AND confidence <= 1', name='ck_job_confidence'),
    )

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('job_sources.id'), nullable=False, index=True)
    slug = db.Column(db.String(320), nullable=False, unique=True, index=True)
    external_id = db.Column(db.String(300), nullable=True)
    content_hash = db.Column(db.String(64), nullable=False, unique=True, index=True)
    title = db.Column(db.String(500), nullable=False)
    organization = db.Column(db.String(500), nullable=False)
    job_type = db.Column(db.String(30), nullable=False, default='government', index=True)
    appointment_type = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(300), nullable=True)
    qualification = db.Column(db.String(600), nullable=True)
    age_limit = db.Column(db.String(300), nullable=True)
    application_fee = db.Column(db.String(300), nullable=True)
    fee_factors = db.Column(db.JSON, nullable=True)
    fee_rules = db.Column(db.JSON, nullable=True)
    fee_rules_verified_at = db.Column(db.DateTime, nullable=True)
    vacancies = db.Column(db.String(200), nullable=True)
    salary = db.Column(db.String(300), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    issue_date = db.Column(db.Date, nullable=True)
    application_start_date = db.Column(db.Date, nullable=True)
    deadline = db.Column(db.Date, nullable=True, index=True)
    official_notice_url = db.Column(db.String(1200), nullable=False)
    application_url = db.Column(db.String(1200), nullable=True)
    status = db.Column(db.String(30), nullable=False, default='needs_review', index=True)
    verification_status = db.Column(db.String(60), nullable=False, default='official_source_checked')
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    is_featured = db.Column(db.Boolean, nullable=False, default=False, index=True)
    first_seen_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    last_seen_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    source = db.relationship('JobSource', back_populates='jobs')

    @property
    def is_open(self):
        return self.deadline is None or self.deadline >= date.today()

    def to_dict(self, include_admin=False):
        data = {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'organization': self.organization,
            'job_type': self.job_type,
            'appointment_type': self.appointment_type,
            'location': self.location,
            'qualification': self.qualification,
            'age_limit': self.age_limit,
            'application_fee': self.application_fee,
            'fee_factors': self.fee_factors or [],
            'fee_rules_verified': bool(self.fee_rules_verified_at),
            'vacancies': self.vacancies,
            'salary': self.salary,
            'summary': self.summary,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'application_start_date': self.application_start_date.isoformat() if self.application_start_date else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'official_notice_url': self.official_notice_url,
            'application_url': self.application_url,
            'status': self.status,
            'verification_status': self.verification_status,
            'is_featured': bool(self.is_featured),
            'source': {
                'key': self.source.key,
                'name': self.source.name,
                'listing_url': self.source.listing_url,
            } if self.source else None,
            'first_seen_at': self.first_seen_at.isoformat() if self.first_seen_at else None,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
        }
        if include_admin:
            data.update({
                'source_id': self.source_id,
                'external_id': self.external_id,
                'content_hash': self.content_hash,
                'confidence': float(self.confidence or 0),
                'fee_rules': self.fee_rules or [],
                'fee_rules_verified_at': self.fee_rules_verified_at.isoformat() if self.fee_rules_verified_at else None,
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            })
        return data
