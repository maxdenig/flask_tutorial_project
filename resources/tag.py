from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from models import StoreModel, TagModel, ItemModel
from schemas import TagSchema, TagAndItemSchema
from db import db
from sqlalchemy.exc import SQLAlchemyError

bp = Blueprint("tags", __name__, description="Operations for Tags")


@bp.route("/store/<int:store_id>/tag")
class TagInStore(MethodView):
    @bp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)
        return store.tags.all()
    
    @jwt_required()
    @bp.arguments(TagSchema)
    @bp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        if TagModel.query.filter(TagModel.store_id == store_id,
                                 TagModel.name == tag_data["name"]).first():
            abort(400, message="A Tag with that name already exists in this Store.")
        tag = TagModel(**tag_data, store_id=store_id)
        try:
            db.session.add(tag)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return tag


@bp.route("/tag/<int:tag_id>")
class Tag(MethodView):
    @bp.response(200, TagSchema)
    def get(self, tag_id):
        return TagModel.query.get_or_404(tag_id)
    
    @jwt_required()
    @bp.response(202, 
                 description="Deletes a tag if no item is attached.",
                 example={"message": "Tag deleted."})
    @bp.alt_response(404, 
                     description="Tag not found.")
    @bp.alt_response(400, 
                     description="Failed because one or more items is attached to this tag. Tag not deleted.")
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)
        if not tag.items:
            try:
                db.session.delete(tag)
                db.session.commit()
                return {"message": "Tag deleted."}
            except SQLAlchemyError as e:
                abort(500, message=str(e))
        abort(400,
              message="Couldn't delete Tag. Unlink all items from it.")
       

@bp.route("/tag")
class TagList(MethodView):
    @bp.response(200, TagSchema(many=True))
    def get(self):
        return TagModel.query.all()


@bp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkItemToTag(MethodView):
    @jwt_required()
    @bp.response(201, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        if item.store_id != tag.store_id:
            abort(400,
                  message="Store ID is not the same for this Tag and Item.")

        try:
            item.tags.append(tag)
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return tag
    
    @jwt_required()
    @bp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)
        try:
            item.tags.remove(tag)
            db.session.add(item)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return {"message": "Item unlinked from tag", "item": item, "tag": tag}
    