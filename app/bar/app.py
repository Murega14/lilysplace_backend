from flask import Blueprint, make_response, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models import DRINK_TYPES, DRINK_VOLUME, PAYMENT_METHODS, Drink, DrinkPurchases, DrinkSales, OpenBottle, Staff, TotSales, db
from app.extensions import logger

bar_bp = Blueprint('bar_bp', __name__, url_prefix='/api/v1')

@bar_bp.route('/drinks/add', methods=['POST'])
@jwt_required()
def add_drinks():
    try:
        data = request.get_json()
        name = data.get('name').strip()
        drink_type = data.get('category')
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
    
@bar_bp.route('/drinks', methods=['GET'])
@jwt_required()
def list_drinks():
    try:
        drinks = Drink.query.all()
        
        drinks_list = [{
            "id": d.id,
            "name": d.name,
            "bottle_size": d.volume,
            "category": d.drink_type,
            "stock": d.stock,
            "selling_price": d.purchase_price * d.markup
        } for d in drinks]
        
        return make_response({'success': False, 'drinks': drinks_list}, 200)
    
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    

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
    
@bar_bp.route('/drinks/<int:drink_id>/sell/retail', methods=['POST'])
@jwt_required()
def sell_drink(drink_id: int):
    try:
        drink = Drink.query.get(drink_id)
        if not drink:
            return make_response({'success': False, 'msg': 'drink not found'}, 404)
        
        if drink.stock == 0:
            return make_response({'success': False, 'msg': 'drink is currently not in stock'}, 400)
        
        data = request.get_json()
        quantity = int(data.get('quantity'))
        payment_method = data.get('payment_method')
        reference_number = data.get('reference_number', None)
        
        if quantity <= 0:
            return make_response({'success': False, 'msg': 'quantity sold cannot be zero'}, 400)
        
        if quantity > drink.stock:
            return make_response({'success': False, 'msg': 'not enough bottles in stock'}, 400)
        
        if payment_method not in PAYMENT_METHODS:
            return make_response({'success': False, 'msg': f'payment can only be made via {', '.join(PAYMENT_METHODS)}'}, 400)
        
        user_id = get_jwt_identity()
        staff = Staff.query.filter_by(user_id=int(user_id)).first()
        
        markup = drink.markup
        vat = 0.16
        
        margin_amount = drink.purchase_price * markup
        net_sales_price = margin_amount + drink.purchase_price
        vat_charge = net_sales_price * vat
        unit_selling_price  = net_sales_price + vat_charge
        total_amount = round(unit_selling_price * quantity, 1)
        
        try:
            new_drink_sale = DrinkSales(
                drink_id=drink_id,
                quantity=quantity,
                sale_type='retail',
                payment_method=payment_method,
                reference_number=reference_number,
                amount=total_amount,
                sold_by=staff.id
            )
            db.session.add(new_drink_sale)
            
            drink.stock -= quantity
            
            db.session.commit()
            
            logger.info(f"new sale recorded for {quantity} bottles of {drink.name}", extra={'user_id': get_jwt_identity()})
            return make_response({"success": True, "msg": "sale recorded successfully"})
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"database error occured trying to record a drink sale: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to record sale, please try again'}, 500)
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"unique constraint violation: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'payment reference number already exists'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
        
                
@bar_bp.route('/drinks/open-bottle/<int:drink_id>', methods=['POST'])
@jwt_required()
def open_bottle(drink_id: int):
    try:
        drink = Drink.query.get(drink_id)
        if not drink:
            return make_response({'msg': 'drink does not exist'}, 404)
        
        try:
            bottles_remaining = drink.stock
            drink.stock = bottles_remaining - 1
            
            open_bottle = OpenBottle(drink_id=drink_id, remaining_shots=drink.shot_quantity)
            db.session.add(open_bottle)
            db.session.commit()
            
            logger.info(f"a new bottle {drink_id} has been opened", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'bottle opened successfully'}, 201)
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"unique constraint violation: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'this bottle has already been opened'}, 500)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"a database error occured trying to open a bottle: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'Failed to open a bottle, please try again'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)

@bar_bp.route('/drinks/open-bottle', methods=['GET'])
@jwt_required()
def list_open_bottles():
    try:
        open_bottles = OpenBottle.query.all()
        
        open_bottle_list = [{
            "id": op.id,
            "name": op.drinks.name,
            "shots_remaining": op.shots_remaining,
            "shot_price": op.drinks.shot_price
        }for op in open_bottles]
        
        return make_response({'success': True, 'open_bottles': open_bottle_list}, 200)
    
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    
@bar_bp.route('/drinks/sell-tot/<int:bottle_id>', methods=['POST'])
@jwt_required()
def sell_tots(bottle_id: int):
    try:
        open_bottle = OpenBottle.query.get(bottle_id)
        if not open_bottle:
            return make_response({'success': False, 'msg': 'bottle not found'}, 404)
        
        data = request.get_json()
        shot_quantity = int(data.get('shot_quantity'))
        payment_method = data.get('payment_method')
        reference_number = data.get('reference_number', None)
        
        staff = Staff.query.filter(and_(
            Staff.user_id == int(get_jwt_identity()), Staff.department == 'bar'
        )).first()
        if not staff:
            return make_response({'success': False, 'msg': 'invalid staff details'}, 400)
        
        if payment_method not in PAYMENT_METHODS:
            return make_response({'success': False, 'msg': f'payment can only be made via {', '.join(PAYMENT_METHODS)}'}, 400)
        
        if shot_quantity <= 0:
            return make_response({'success': False, 'msg': 'shots sold cannot be zero'}, 400)
        
        try:
            price = shot_quantity * open_bottle.drink.shot_price
            new_tot_sale = TotSales(
                open_bottle_id=bottle_id,
                shot_quantity=shot_quantity,
                price=price,
                payment_method=payment_method,
                reference_number=reference_number,
                sold_by=staff.id
            )
            db.session.add(new_tot_sale)
            
            open_bottle.shots_remaining -= shot_quantity
            
            if open_bottle.shots_remaining == 0:
                db.session.delete(open_bottle)
                logger.info(f"open bottle {open_bottle.drink.name} is now finished", extra={'user_id': get_jwt_identity()})
            
            db.session.commit()
            
            logger.info(f"{shot_quantity} shots of {open_bottle.drink.name} sold", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'sale recorded successfully'}, 201)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"a database error occured trying to record a shot sale: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to record sale, please try again'}, 500)
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"unique constraint violation: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'payment reference number already exists'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    
@bar_bp.route('drinks/tot-sales/<int:sale_id>/edit', methods=['PUT'])
@jwt_required()
def edit_tot_sale(sale_id: int):
    try:
        sale = TotSales.query.get(sale_id)
        if not sale:
            return make_response({'success': False, 'msg': 'sale record does not exist'}, 404)
        
        data = request.get_json()
        try:
            if 'bottle_id' in data or 'shot_quantity' in data:
            
                original_bottle = OpenBottle.query.get(sale.open_bottle_id)
                if original_bottle:
                    original_bottle.shots_remaining += sale.shot_quantity
                
                new_bottle_id = data.get('bottle_id', sale.open_bottle_id)
                new_quantity = int(data.get('shot_quantity')) if data['shot_quantity'] is not None else sale.shot_quantity 

                target_bottle = OpenBottle.query.get(new_bottle_id)
                
                if not target_bottle:
                    return make_response({'success': False, 'msg': 'Target bottle not found'}, 404)

                
                if target_bottle.shots_remaining < new_quantity:
                    db.session.rollback() 
                    return make_response({'success': False, 'msg': 'Insufficient shots remaining in the selected bottle'}, 400)

                target_bottle.shots_remaining -= new_quantity

                sale.open_bottle_id = new_bottle_id
                sale.shot_quantity = new_quantity
                
                sale.price = target_bottle.drink.shot_price * new_quantity
                
            if 'payment_method' in data:
                if data['payment_method'] not in PAYMENT_METHODS:
                    return make_response({'success': False, 'msg': f'payment can only be done via {', '.join(PAYMENT_METHODS)}'}, 400)
                
                sale.payment_method = data['payment_method']
                
            if 'reference_number' in data:
                sale.reference_number = data['reference_number']
                
            db.session.commit()
            
            logger.info(f"tot sale {sale_id} has been edited", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'sale record has been edited successfully'}, 200)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"a database error occured trying to edit a tot sale record: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to edit sale record, please try again'}, 500)
        
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"unique constraint violation: {str(e)}", extra={'user_id': get_jwt_identity})
            return make_response({'success': False, 'msg': 'payment reference number exists'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
        
    
@bar_bp.route('/drinks/record-purchase/<int:drink_id>', methods=['POST'])
@jwt_required()
def record_drink_purchase(drink_id: int):
    try:
        drink = Drink.query.get(drink_id)
        if not drink:
            return make_response({'success': False, 'msg': 'drink not found'}, 404)
        
        data = request.get_json()
        quantity = int(data.get('quantity'))
        unit_price = float(data.get('unit_price'))
        payment_method = data.get('payment_method')
        reference_number = data.get('reference_number', None)
        supplier = data.get('supplier')
        
        if quantity <= 0:
            return make_response({'success': False, 'msg': 'quantity purchased cannot be zero'}, 400)
        
        if unit_price <= 0:
            return make_response({'success': False, 'msg': 'unit price for purchased stock cannot be zero'}, 400)
        
        if payment_method not in PAYMENT_METHODS:
            return make_response({'success': False, 'msg': f'payment method can only be {', '.join(PAYMENT_METHODS)}'}, 400)
        
        try:
            new_purchase = DrinkPurchases(
                drink_id=drink_id,
                quantity=quantity,
                unit_price=unit_price,
                payment_method=payment_method,
                reference_number=reference_number,
                supplier=supplier
            )
            db.session.add(new_purchase)
            drink.stock += quantity
            drink.purchase_price = unit_price
            db.session.commit()
            
            logger.info(f"new purchase recorded for {drink.name}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': True, 'msg': 'drink purchase recorded successfully'}, 201)
        
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"a database error occured trying to add a purchase record: {str(e)}", extra={'user_id': get_jwt_identity()})
            return make_response({'success': False, 'msg': 'failed to record drink purchase, please try again'}, 500)
        
    except Exception as e:
        logger.error(f"an error occured: {str(e)}", extra={'user_id': get_jwt_identity()})
        return make_response({'success': False, 'msg': 'internal server error'}, 500)
    