import os
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
from app.routes.class_routes import class_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Swagger setup
    Swagger(app)

    # Enable CORS (for frontend) - support both localhost and production
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ]

    # Add production frontend URL if set
    frontend_url = os.environ.get('FRONTEND_URL')
    if frontend_url:
        allowed_origins.append(frontend_url)

    CORS(app,
         resources={r"/*": {
             "origins": allowed_origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "expose_headers": ["Content-Type", "Authorization"],
             "send_wildcard": False,
             "always_send": True
         }}
    )

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
    app.register_blueprint(class_bp)

    # Health check endpoint
    @app.route('/health')
    def health():
        return {"status": "ok"}
    
    with app.app_context():
        print("\n🚀 Registered Flask Routes:")
        for rule in app.url_map.iter_rules():
            methods = ','.join(rule.methods)
            print(f"{rule.endpoint:30s} {methods:20s} {rule}")

    return app


# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
