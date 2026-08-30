from ..utils.database import db
from datetime import datetime, timezone
def utc_now(): return datetime.now(timezone.utc).replace(tzinfo=None)


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)


class PlatformSetting(db.Model):
    """Small, non-secret settings that must survive catalog reseeding."""
    __tablename__ = 'platform_settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.String(500), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=utc_now, onupdate=utc_now)


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text)
    price_inr = db.Column(db.Float, default=0.0)
    official_fee_inr = db.Column(db.Float, nullable=True)
    official_fee_status = db.Column(db.String(20), nullable=False, default='unconfirmed')
    keywords = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    def to_dict(self):
        from ..utils.seo import application_service_name, slugify
        display_name = application_service_name(self.name)
        return {
            'id': self.id,
            'slug': slugify(display_name),
            'name': display_name,
            'description': self.description,
            'price_inr': float(self.price_inr or 0.0),
            'official_fee_inr': float(self.official_fee_inr) if self.official_fee_inr is not None else None,
            'official_fee_status': self.official_fee_status or 'unconfirmed',
            'keywords': self.keywords or '',
            'category': self.category.name if self.category else None,
            'category_id': self.category_id,
            'is_active': bool(self.is_active)
        }
