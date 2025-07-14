from .auth import auth_bp
# from .agent import agent_bp
# from .workflow import workflow_bp
# from .monitoring import monitoring_bp
# from .orchestration import orchestration_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    # app.register_blueprint(agent_bp, url_prefix="/api/agents")
    # app.register_blueprint(workflow_bp, url_prefix="/api/workflows")
    # app.register_blueprint(monitoring_bp, url_prefix="/api/monitoring")
    # app.register_blueprint(orchestration_bp, url_prefix="/api/orchestration") 