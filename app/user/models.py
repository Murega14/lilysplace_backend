from app.models import AuditMixin, db
from werkzeug.security import generate_password_hash, check_password_hash

class User(AuditMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    role = db.Column(db.Enum('bar', 'restaurant', 'carwash', 'manager'), nullable=False)
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
    id_number = db.Column(db.String(8), unqiue=True, nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)
    department = db.Column(db.Enum('bar', 'restaurant', 'carwash', 'manager'))
    
    user = db.relationship('User', backref='staff', cascade="all,delete")