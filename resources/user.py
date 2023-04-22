from flask.views import MethodView
from flask_smorest import Blueprint, abort
from models import UserModel
from schemas import UserSchema
from sqlalchemy.exc import SQLAlchemyError
from db import db
from passlib.hash import pbkdf2_sha256 as hash_alg
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required, get_jwt
from blocklist import BLOCKLIST

bp = Blueprint("users", __name__, description="Operations for Users")


@bp.route("/user/<int:user_id>")
class User(MethodView):
    @bp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user

    @jwt_required()
    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."}


@bp.route("/user")
class UserRegister(MethodView):
    @bp.response(200, UserSchema(many=True))
    def get(self):
        return UserModel.query.all()
    
    @bp.arguments(UserSchema)
    @bp.response(201, 
                 description="User created successfully.",
                 example="User created successfully.")
    def post(self, user_data):
        user = UserModel(
            username=user_data["username"],
            password=hash_alg.hash(user_data["password"])
            )
        try:
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError as e:
            abort(500, message=str(e))
        return {"message": "User created successfully."}


@bp.route("/login")
class UserLogin(MethodView):
    @bp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and hash_alg.verify(user_data["password"], user.password):
            access_tkn = create_access_token(identity=user.id, fresh=True)
            refresh_tkn = create_refresh_token(identity=user.id)
            return {"access_token": access_tkn, "refresh_token": refresh_tkn}

        abort(401, message="Invalid credentials.")


@bp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out."}


@bp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"access_token": new_token}
    