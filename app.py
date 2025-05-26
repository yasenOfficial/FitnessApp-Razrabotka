# ╔═════════════════════════════════════════════╗
# ║  I HAVE SPENT 500 HOURS ON THIS JUNGLE 🕳️   ║
# ║  When I wrote this code, only I and God     ║
# ║  knew how it worked... now only God does.   ║
# ║  Don't waste your time here—just scroll on. ║
# ║  If you're still reading, bump the counters:║
# ║    hoursWasted += 1;                        ║
# ║    sanityLevel    -= 1;                     ║
# ╚═════════════════════════════════════════════╝

from flask import Flask, send_file
from config import Config
from extensions import init_extensions, db, jwt
from flask_swagger_ui import get_swaggerui_blueprint

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    # Initialize extensions
    init_extensions(app)

    # Register web blueprints
    from routes import blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # Register API blueprint
    from routes.api.v1 import api_v1
    app.register_blueprint(api_v1)

    # Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = '/static/swagger.yaml'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "GameFit API Documentation"
        }
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    @app.route('/static/swagger.yaml')
    def send_swagger_spec():
        return send_file('swagger.yaml')

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
