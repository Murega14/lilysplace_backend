from flask import Blueprint, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError
from app.models import DRINK_TYPES, DRINK_VOLUME, Drink, db
from app.extensions import logger

bar_bp = Blueprint('bar_bp', __name__, url_prefix='/api/v1')

@bar_bp.route('/drinks/add', methods=['POST'])
@jwt_required()
def add_drinks():
    try:
        data = request.get_json()
        name = data.get('name').strip()
        drink_type = data.get('drink_type')
        stock = data.get('stock')
        purchase_price = data.get('purchase_price')
        volume = data.get('volume')
        markup = float(data.get('markup'))
        shot_price = data.get('shot_price')
        shot_quantity = data.get('shot_quantity')
        
        if drink_type not in DRINK_TYPES:
            return make_response({'success': False, 'msg': f"drink types can only be one of: {', '.join(DRINK_TYPES)}"}, 400)
        
        if volume not in DRINK_VOLUME:
            return make_response({'success': False, 'msg': f"drink volume can only be {', '.join(DRINK_VOLUME)}"}, 400)
        
        if stock <= 0:
            return make_response({"success": False, "msg": "stock cannot be zero or less than zero"}, 400)
        
        if purchase_price <= 0:
            return make_response({"success": False, "msg": "purchase price cannot be or less than zero"}, 400)
        
        if markup <= 0.0:
            return make_response({'success': False, 'msg': 'markup cannot be less than or equal to zero'}, 400)
        
        try:
            new_drink = Drink(
                name=name, drink_type=drink_type, stock=stock, purchase_price=purchase_price, volume=volume, markup=markup, shot_price=shot_price, shot_quantity=shot_quantity
            )
            db.session.add(new_drink)
            db.session.commit()
            
            logger.info(f"new drink {name}, {volume}: {stock} units has been added", extra={'user_id': get_jwt_identity()})
            return make_response({"success": True, "msg": "drink added successfully"}, 201)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"a database error occured trying to add a new drink: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to add drink, please try again'}, 500)
    
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({"success": False, "msg": "internal server error"}, 500)
    

@bar_bp.route('/drinks/<int:drink_id>/edit', methods=['PUT'])
@jwt_required()
def edit_drinks(drink_id: int):
    try:
        drink = Drink.query.get(drink_id)
        if not drink:
            return make_response({'success': False, 'msg': 'drink not found'}, 404)
        
        data = request.get_json()
        
        try:
            if 'name' in data:
                drink.name = data['name']
                
            if 'drink_type' in data:
                if data['drink_type'] in DRINK_TYPES:
                    drink.drink_type = data['drink_type']
                else:
                    return make_response({'success': False, 'msg': f'drink types can only be on of {', '.join(DRINK_TYPES)}'}, 400)
                
            if 'stock' in data:
                drink.stock = int(data['stock'])
                
            if 'purchase_price' in data:
                drink.purchase_price = data['purchase_price']
            
            if 'markup' in data:
                drink.markup = float(data['markup'])
            
            if 'volume' in data:
                if data['volume'] in DRINK_VOLUME:
                    drink.volume = data['volume']
                else:
                    return make_response({'success': False, 'msg': f'volume can only be one of {', '.join(DRINK_VOLUME)}'}, 400)
                
            if 'shot_price' in data:
                drink.shot_price = float(data['shot_price'])
            
            if 'shot_quantity' in data:
                drink.shot_quantity = data['shot_quantity']
                
            db.session.commit()
            logger.info(f"drink {drink_id} has been updated", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'drink details have been updated successfully'}, 200)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error occured when trying to update drink details: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to update drink details, please try again'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured when trying to update drink details: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)

@bar_bp.route('/drinks/<int:drink_id>/delete', methods=['DELETE'])
@jwt_required()
def delete_drink(drink_id: int):
    try:
        drink = Drink.query.get(drink_id)
        if not drink:
            return make_response({'success': False, 'msg': 'drink does not exist'}, 404)
        
        try:
            db.session.delete(drink)
            db.session.commit()
            
            logger.info(f"drink {drink.name}, {drink.volume} has been deleted", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'drink has been deleted'}, 200)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error occured when trying to delete drink: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to delete drink, please try again'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured when trying to delete a drink: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
                