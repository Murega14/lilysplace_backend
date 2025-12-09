from datetime import timedelta
from flask import Blueprint, make_response, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app.extensions import logger
from app.models import User, db
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError

login_bp = Blueprint('login_bp', __name__, url_prefix="/api/v1")

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            expiry = timedelta(hours=2)
            access_token = create_access_token(identity=str(user.id), expires_delta=expiry)
            
            response = make_response({
                'success': True,
                'msg': 'login successful',
                'access_token': access_token
            }, 200)
            response.set_cookie(access_token, samesite='Lax', secure=True, httponly=True)
            
            logger.info(f"{user.id} logged in", extra={'user_id': user.id})
            return response
        
        else:
            return make_response({'success': False, 'msg': 'invalid login credentials'}, 400)
    
    except Exception as e:
        logger.error(f"an error occurred during login: {str(e)}")
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    
@login_bp.route('/change-password', methods=['PATCH'])
@jwt_required()
def change_password():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))
        
        data = request.get_json()
        new_password = data.get('new_password')
        
        hashed_new_password = generate_password_hash(new_password) 
        if hashed_new_password == user.password_hash:
            return make_response({'success': False, 'msg': 'new password cannot be the same as the old password'}, 400)
        
        try:
            user.hash_password(new_password)
            db.session.commit()
            
            logger.info(f"user {user_id} has changed their password")
            return make_response({'success': True, 'msg': 'password updated successfully'}, 200)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error occured when trying to update user password: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to update password, please try again'}, 500)
    
    except Exception as e:
        logger.error(f"an error occured trying to change user password: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)