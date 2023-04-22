from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from models import StoreModel
from schemas import StoreSchema
from db import db
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

bp = Blueprint("stores", __name__, description="Operations for Stores")


@bp.route("/store/<int:store_id>")
class Store(MethodView):
    @bp.response(200, StoreSchema)
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store

    @jwt_required(fresh=True)
    def delete(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        db.session.delete(store)
        db.session.commit()
        return {"message": "Store deleted."}
    
    @jwt_required()
    @bp.arguments(StoreSchema)
    @bp.response(200, StoreSchema)
    def put(self, store_data, store_id):
        store = StoreModel.query.get(store_id)
        if store:
            store.name = store_data["name"]
        else:
            store = StoreModel(id=store_id, **store_data)

        db.session.add(store)
        db.session.commit()
        return store


@bp.route("/store")
class StoreList(MethodView):
    @bp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()
    
    @jwt_required(fresh=True)
    @bp.arguments(StoreSchema)
    @bp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)
        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            abort(400, message="A Store with this name already exists.")
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return store
    