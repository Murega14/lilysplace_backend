from flask import Blueprint, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_
from app.models import db
from app.user.models import Staff, User
from app.extensions import logger
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

register_bp = Blueprint('register_bp', __name__, url_prefix='/api/v1')

@register_bp.route('/create-staff', methods=['POST'])
@jwt_required()
def register_staff():
    try:
        data = request.get_json()
        name = data.get('name')
        phone_number = data.get('phone_number')
        id_number = data.get('id_number')
        department = data.get('department').lower()
        
        if len(id_number) > 8:
            return make_response({'success': False, 'msg': 'id number should be 8 digits'}, 400)
        
        if department not in ['bar', 'carwash', 'restaurant', 'manager']:
            return make_response({"success": False, "msg": "department can only be bar, carwash, restaurant or manager"}, 400)
        
        if len(phone_number) > 10:
            return make_response({'success': False, 'msg': 'phone number can only be 10 digits, start with 07 or 011'}, 400)
        
        try:
            new_user = User(username=phone_number, role=department)
            new_user.hash_password(id_number)
            db.session.add(new_user)
            db.session.flush()
            
            new_staff = Staff(name=name, phone_number=phone_number, id_number=id_number, department=department, user_id=new_user.id)
            db.session.add(new_staff)
            db.session.commit()
            
            logger.info(f"new staff and user profile created: {new_user.id}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'new staff and user profile created successfully'}, 201)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error trying to create staff profile: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to create staff profile, please try again'}, 500)
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"database integrity error: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'id number or phone number already exists'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured trying to create a staff profile: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'Internal Server Error'}, 500)
    
@register_bp.route('/delete-staff/<int:staff_id>', methods=['DELETE'])
@jwt_required()
def delete_user(staff_id: int):
    try:
        admin_id = get_jwt_identity()
        admin = User.query.filter(and_(
            User.id == admin_id, User.role == 'manager'
        ))
        if not admin:
            return make_response({'success': False, 'msg': 'only admins can perform this action'}, 400)
        
        staff_to_be_deleted = Staff.query.get(staff_id)
        if not staff_to_be_deleted:
            return make_response({'success': False, 'msg': 'staff member does not exist'}, 404)
        
        try:
            db.session.delete(staff_to_be_deleted)
            db.session.commit()
            
            logger.info(f"staff {staff_id} profile has been deleted", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'staff profile has been deleted successfully'}, 200)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error when trying to delete staff profile: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({"success": False, "msg": "failed  to delete staff profile"}, 500)
    
    except Exception as e:
        logger.error(f"an error occured trying to delete staff profile: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    

            