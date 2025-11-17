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
            return make_response({'success': False, 'msg': 'payment reference number exists'}, 400)
        
    except Exception as e:
        logger.error(f"an error occured trying to record carwash income: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    
@carwash_bp.route('/carwarsh/income/<id:income_id>/edit', methods=['PUT'])
@jwt_required()
def edit_carwash_income(income_id: int):
    try:
        carwash_income = CarwashIncome.query.get(income_id)
        if not carwash_income:
            return make_response({'success': False, 'msg': 'income record not found'}, 404)
        
        data = request.get_json()
        
        try:
            if 'customer' in data:
                carwash_income.customer = data['cutomer']
            
            if 'staff_id' in data:
                staff = Staff.query.filter(and_(
                    Staff.id == data['staff_id'], staff.department == 'carwash'
                )).first()
                if staff:
                    carwash_income.staff_id = data['staff_id']
                else:
                    return make_response({'success': False, 'msg': 'staff not found'}, 404)
            
            if 'amount_charged' in data:
                carwash_income.amount_charged = float(data['amount_charged'])
            
            if 'payment_method' in data:
                if data['payment_method'] in PAYMENT_METHODS:
                    carwash_income.payment_method = data['payment_method']
                else:
                    return make_response({'success': False, 'msg': f'payment method can only be: {', '.join(PAYMENT_METHODS)}'}, 400)
                
            if 'payment_reference_number' in data:
                carwash_income.payment_reference_number = data['reference_number']
                
            if 'service' in data:
                if data['service'] in SERVICE_TYPES:
                    carwash_income.service = data['service']
                else:
                    return make_response({'success': False, 'msg': f'service can only be one of {', '.join(SERVICE_TYPES)}'}, 400)
                
            if 'date' in data:
                try:
                    formatted_date = datetime.strftime(data['date'], '%d-%m-%Y, %H:%M')
                    carwash_income.date = formatted_date
                except ValueError:
                    return make_response({'success': False, 'msg': 'invalid date format'}, 400)
            
            db.session.commit()
            logger.info(f"carwash income entry {carwash_income.id} has been updated", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'income entry updated successfully'}, 200)

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"a database error occured trying to update a carwash income entry: {str(e)}", extra={'useer_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to update entry, please try again'}, 400)
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"unique constraint violation trying to update carwash income: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'payment reference number already exists'}, 400)
        
    except Exception as e:
        logger.error(f"an error occured trying to update carwash income entry: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    
@carwash_bp.route('/carwash/income/<int:income_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_carwash_income(income_id):
    try:
        carwash_income = CarwashIncome.query.get(income_id)
        if not carwash_income:
            return make_response({'success': False, 'msg': 'income record not found'}, 404)
        
        try:
            db.session.delete(carwash_income)
            db.session.commit()
            
            logger.info(f"carwash income record {income_id} deleted", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'income entry deleted successfully'}, 200)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error occured trying to delete a record of carwash income: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to delete carwash income record, please try again'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured trying to delete an income record: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)