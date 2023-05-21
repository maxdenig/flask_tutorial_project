import os
from sqlalchemy import or_

import requests
from flask.views import MethodView
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt, get_jwt_identity, jwt_required)
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256 as hash_alg
from sqlalchemy.exc import SQLAlchemyError

from blocklist import BLOCKLIST
from db import db
from models import UserModel
from schemas import UserSchema, UserRegisterSchema

bp = Blueprint("users", __name__, description="Operations for Users")


def send_simple_message(to, subj, body):
    domain = os.getenv("MAILGUN_DOMAIN")
    api_key = os.getenv("MAILGUN_API_KEY")
    return requests.post(
		f"https://api.mailgun.net/v3/{domain}/messages",
		auth=("api", api_key),
		data={"from": f"Excited User <mailgun@{domain}>",
			"to": [to],
			"subject": subj,
			"text": body})


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
    
    @bp.arguments(UserRegisterSchema)
    @bp.response(201, 
                 description="User created successfully.",
                 example="User created successfully.")
    def post(self, user_data):

        if UserModel.query.filter(
            or_(
                UserModel.username == user_data["username"],
                UserModel.email == user_data["email"]
                )
        ).first():
            abort(409, message="A user with this username or email already exists.")

        user = UserModel(
            username=user_data["username"],
            email=user_data["email"],
            password=hash_alg.hash(user_data["password"])
            )
        try:
            db.session.add(user)
            db.session.commit()
            send_simple_message(
                to=user.email,
                subj="Successfully registered",
                body=f"Hello {user.username}, you have been successfully registered."
            )
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
    