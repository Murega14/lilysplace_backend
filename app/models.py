from email.policy import default
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from werkzeug.security import generate_password_hash, check_password_hash

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(table_name)s_%(column_0_name)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

db = SQLAlchemy(metadata=metadata)

class AuditMixin:
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=True, onupdate=db.func.current_timestamp())
    
DRINK_TYPES = [
    'Whiskey', 'Beer', 'Vodka', 'Gin', 'LiqueUr', 'Wine',
    'Spirit', 'Rum', 'Brandy', 'Cognac', 'Cider', 'Tequila'
]

DRINK_VOLUME = ['250 ml', '350 ml', '500 ml', '750 ml', '1L']

SERVICE_TYPES = []

PAYMENT_METHODS = ['mpesa', 'bank payment', 'cash']

class User(AuditMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    role = db.Column(db.Enum('bar', 'restaurant', 'carwash', 'manager', name='user_role'), nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    
    def hash_password(self, password):
       self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
        
class Staff(db.Model, AuditMixin):
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String, nullable=False)
    id_number = db.Column(db.String(8), unique=True, nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)
    department = db.Column(db.Enum('bar', 'restaurant', 'carwash', 'manager', name='staff_department'))
    
    user = db.relationship('User', backref='staff', cascade="all,delete")

class Drink(db.Model, AuditMixin):
    __tablename__ = 'drinks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    drink_type = db.Column(db.Enum(*DRINK_TYPES, name='drinks_type'), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    purchase_price = db.Column(db.Float, nullable=False)
    volume = db.Column(db.Enum(*DRINK_VOLUME, name='drink_volume'), nullable=False)
    markup = db.Column(db.Float, nullable=False)
    shot_price = db.Column(db.Float, nullable=False)
    shot_quantity = db.Column(db.Integer, nullable=False)
    
class CarwashIncome(db.Model, AuditMixin):
    __tablename__ = 'carwash_income'
    
    id = db.Column(db.Integer, primary_key=True)
    customer = db.Column(db.String, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    amount_charged = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.Enum(*PAYMENT_METHODS, name='carwash_payment_method'), nullable=True)
    payment_reference_number = db.Column(db.String, unique=True, nullable=True)
    service = db.Column(db.Enum(*SERVICE_TYPES, name='carwash_service_type'), nullable=False)
    date = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    
    staff = db.relationship('Staff', backref='carwash_income')