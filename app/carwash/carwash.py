from datetime import datetime
from flask import Blueprint, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.extensions import logger
from app.models import PAYMENT_METHODS, SERVICE_TYPES, CarwashIncome, Staff, db

carwash_bp = Blueprint('carwash_bp', __name__, url_prefix='/api/v1')

@carwash_bp.route('/carwash/add-income', method=['POST'])
@jwt_required()
def add_carwash_income():
    try:
        data = request.get_json()
        customer = data.get('customer')
        staff_id = data.get('staff_id')
        amount_charged = float(data.get('amount_charged'))
        payment_method = data.get('payment_method').lower()
        payment_reference_number = data.get('payment_reference_number')
        service = data.get('service')
        date = data.get('date')
        
        staff = Staff.query.filter(and_(
            Staff.id == staff_id, Staff.department == 'carwash'
        )).first()
        if not staff:
            return make_response({'success': False, 'msg': 'staff must exist or be part of the carwash staff'}, 400)
        
        if amount_charged == 0:
            return make_response({'success': False, 'msg': 'amount charged cannot be zero'}, 400)
        
        if payment_method not in PAYMENT_METHODS:
            return make_response({'success': False, 'msg': f"payment methods can only be {', '.join(PAYMENT_METHODS)}"}, 400)
        
        if service not in SERVICE_TYPES:
            return make_response({'success': False, 'msg': f"carwash service can only be {', '.join(SERVICE_TYPES)}"}, 400)
        
        try:
            formatted_date = datetime.strftime(date, '%d-%m-%Y, %H-%M')
        except ValueError:
            return make_response({'success': False, 'msg': 'invalid date format'}, 400)
        
        try:
            new_carwash_income = CarwashIncome(
                customer=customer,
                staff_id=staff_id,
                amount_charged=amount_charged,
                payment_method=payment_method,
                payment_reference_number=payment_reference_number if payment_reference_number else None,
                service=service,
                date=formatted_date
            )
            db.session.add(new_carwash_income)
            db.session.commit()
            
            logger.info(f"new carwash income recorded {new_carwash_income.id}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'carwash income recorded successfully'}, 201)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error recording carwash income: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to record carwash income, please try again'}, 500)
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"unique constraint violation for payment reference number: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'payment reference number exists'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured trying to record carwash income: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)