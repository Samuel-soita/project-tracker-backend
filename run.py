from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from flasgger import Swagger
from app.config import Config
from app.models import db

# Import blueprints
from app.routes.auth_routes import auth_routes
from app.routes.user_routes import user_routes
from app.routes.project_routes import project_routes
from app.routes.cohort_routes import cohort_routes
from app.routes.member_routes import member_routes
from app.routes.activity_routes import activity_routes
from app.routes.task_routes import task_bp  

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Swagger setup
    Swagger(app)

    # Enable CORS (for frontend)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize DB + migrations
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(project_routes)
    app.register_blueprint(cohort_routes)
    app.register_blueprint(member_routes)
    app.register_blueprint(activity_routes)
    app.register_blueprint(task_bp)  

    # Health check endpoint
    @app.route('/health')
    def health():
        return {"status": "ok"}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
