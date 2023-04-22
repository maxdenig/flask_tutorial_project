from flask.views import MethodView
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt
from models import ItemModel
from schemas import ItemSchema, ItemUpdatedSchema
from sqlalchemy.exc import SQLAlchemyError
from db import db

bp = Blueprint("items", __name__, description="Operations for Items")


@bp.route("/item/<int:item_id>")
class Item(MethodView):
    @bp.response(200, ItemSchema)
    def get(self, item_id):
        item = ItemModel.query.get_or_404(item_id)
        return item

    @jwt_required(fresh=True)
    def delete(self, item_id):
        if not get_jwt().get("is_admin"):
            abort(401, message="Admin privilege required.")
            
        item = ItemModel.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        return {"message": "Item deleted."}
    
    @jwt_required(fresh=True)
    @bp.arguments(ItemUpdatedSchema)
    @bp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemModel.query.get(item_id)
        
        if item:
            item.price = item_data["price"]
            item.name = item_data["name"]
        else:
            item = ItemModel(id=item_id, **item_data)

        db.session.add(item)
        db.session.commit()
        return item


@bp.route("/item")
class ItemList(MethodView):
    @bp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()
    
    @jwt_required(fresh=True)
    @bp.arguments(ItemSchema)
    @bp.response(201, ItemSchema)
    def post(self, item_data):
        item = ItemModel(**item_data)
        try:
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return item
