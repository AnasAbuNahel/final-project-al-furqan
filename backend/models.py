from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ---------- Tenant model ----------
class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='tenant', lazy=True)
    residents = db.relationship('Resident', backref='tenant', lazy=True)
    children = db.relationship('Child', backref='tenant', lazy=True)
    imports = db.relationship('Import', backref='tenant', lazy=True)
    exports = db.relationship('Export', backref='tenant', lazy=True)
    notifications = db.relationship('Notification', backref='tenant', lazy=True)

    def __repr__(self):
        return f"<Tenant {self.slug} (id={self.id})>"

# ---------- helper / mixin (optional but convenient) ----------
class TenantMixin:
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False, index=True)

# ---------- User model (belongs to a tenant) ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="admin")
    permissions = db.Column(db.Text, nullable=True)

    # each user belongs to a single tenant (change nullable=True if you want global users)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'tenant_id': self.tenant_id
        }

# ---------- Resident model ----------
class Resident(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    husband_name = db.Column(db.String(100), nullable=True)
    husband_id_number = db.Column(db.String(20), nullable=True)
    wife_name = db.Column(db.String(100), nullable=True)
    wife_id_number = db.Column(db.String(20), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    num_family_members = db.Column(db.Integer, nullable=True)
    injuries = db.Column(db.String(200), nullable=True)
    diseases = db.Column(db.String(200), nullable=True)
    damage_level = db.Column(db.String(200), nullable=True)
    neighborhood = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.String(300), nullable=True)
    has_received_aid = db.Column(db.Boolean, default=False)

    aids = db.relationship('Aid', backref='resident', lazy=True, cascade="all, delete-orphan")

    def serialize(self):
        return {
            'id': self.id,
            'husband_name': self.husband_name,
            'husband_id_number': self.husband_id_number,
            'wife_name': self.wife_name,
            'wife_id_number': self.wife_id_number,
            'phone_number': self.phone_number,
            'num_family_members': self.num_family_members,
            'injuries': self.injuries,
            'diseases': self.diseases,
            'damage_level': self.damage_level,
            'neighborhood': self.neighborhood,
            'notes': self.notes,
            'has_received_aid': self.has_received_aid,
            'tenant_id': self.tenant_id,
            'aid_history': [aid.serialize() for aid in self.aids]
        }

# ---------- Aid model ----------
class Aid(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey('resident.id'), nullable=False)
    aid_type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'resident_id': self.resident_id,
            'aid_type': self.aid_type,
            'date': self.date,
            'tenant_id': self.tenant_id,
            'resident': {
                'husband_name': self.resident.husband_name if self.resident else None,
                'husband_id_number': self.resident.husband_id_number if self.resident else None
            }
        }

# ---------- Notification model ----------
class Notification(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(300), nullable=False)
    target_name = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'target_name': self.target_name,
            'timestamp': self.timestamp.isoformat(),
            'tenant_id': self.tenant_id
        }

# ---------- Import model ----------
class Import(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'source': self.source,
            'name': self.name,
            'date': self.date,
            'type': self.type,
            'amount': self.amount,
            'tenant_id': self.tenant_id
        }

# ---------- Export model ----------
class Export(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(20), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'date': self.date,
            'tenant_id': self.tenant_id
        }

# ---------- Child model ----------
class Child(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    id_number = db.Column(db.String(50), nullable=False)  # unique per-tenant (enforced at app-level)
    birth_date = db.Column(db.String(20), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    benefit_type = db.Column(db.String(100), nullable=False)
    benefit_count = db.Column(db.Integer, default=0)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'id_number': self.id_number,
            'birth_date': self.birth_date,
            'age': self.age,
            'phone': self.phone,
            'gender': self.gender,
            'benefit_type': self.benefit_type,
            'benefit_count': self.benefit_count,
            'tenant_id': self.tenant_id
        }

# ---------- Assistance model ----------
class Assistance(db.Model, TenantMixin):
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'), nullable=False)
    help_type = db.Column(db.String(100), nullable=False)
    other_help = db.Column(db.String(255), nullable=True)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    child = db.relationship('Child', backref=db.backref('assistance', lazy=True))

    def __init__(self, child_id, help_type, other_help=None):
        self.child_id = child_id
        self.help_type = help_type
        self.other_help = other_help

# ---------- helper function for logging (app-level may override) ----------
def log_action(user_info, action, target_name=None):
    """
    Create a Notification linked to the tenant of the acting user.
    user_info is expected to include 'user_id', 'username' and optionally 'tenant_id'.
    """
    tenant_id = user_info.get('tenant_id') if isinstance(user_info, dict) else None
    notification = Notification(
        user_id=user_info.get('user_id') if isinstance(user_info, dict) else None,
        username=user_info.get('username') if isinstance(user_info, dict) else str(user_info),
        action=action,
        target_name=target_name,
        tenant_id=tenant_id or 0  # use 0 or create policy; better to require tenant_id
    )
    db.session.add(notification)
    db.session.commit()
