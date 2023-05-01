import os

from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api
from dotenv import load_dotenv

from blocklist import BLOCKLIST
from db import db
from resources import ItemBp, StoreBp, TagBp, UserBp

# docker run -dp 5001:5000 -w /app -v "/c/repo/flask_api:/app" flask-sqlalchemy

def create_app(db_url=None):
    app = Flask(__name__)
    load_dotenv()

    ## APP CONFIGS ##
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Stores REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    #app.config["SQLALCHEMY_DATABASE_URI"] = db_url or "sqlite:///data.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    ## JWT ##
    app.config["JWT_SECRET_KEY"] = "153515046718717555482273270844057206552"

    jwt = JWTManager(app)
    
    @jwt.token_in_blocklist_loader
    def check_token_blocked(jwt_header, jwt_payload):
        return jwt_payload["jti"] in BLOCKLIST
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {"description": "Token has been revoked.",
                 "error": "token_revoked"}
            ),
            401
        )
    
    @jwt.needs_fresh_token_loader
    def token_not_freash_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {"description": "Token is not fresh.",
                 "error": "fresh_token_required"}
            ),
            401
        )

    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        if identity == 1:
            return {"is_admin": True}
        return {"is_admin": False}

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return(
            jsonify(
                {"message": "Token has expired.",
                "error": "token_expired"}
             ),
             401
        )
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {"message": "Signature verification failed.",
                 "error": "invalid_token"}
            ),
            401
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {"description": "Request missing access token.",
                 "error": "authorization_required"}
            ),
            401
        )

    ## DB INITIALIZATION ##
    db.init_app(app)

    #with app.app_context():
    #    db.create_all()

    ## MIGRRATION INITIALIZATION ##
    migrate = Migrate(app, db)

    ## API INITIALIZATION ##
    api = Api(app)

    api.register_blueprint(ItemBp)
    api.register_blueprint(StoreBp)
    api.register_blueprint(TagBp)
    api.register_blueprint(UserBp)

    return app
