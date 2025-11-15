from datetime import timedelta
from flask import Blueprint, make_response, request
from flask_jwt_extended import create_access_token, get_jwt_identity
from app.extensions import logger
from app.user.models import User


login_bp = Blueprint('login_bp', __name__, url_prefix="/api/v1")

@login_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username)
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
        logger.error(f"an error occurred during login: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)