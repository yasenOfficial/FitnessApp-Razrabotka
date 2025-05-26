# ╔═════════════════════════════════════════════╗
# ║  I HAVE SPENT 500 HOURS ON THIS JUNGLE 🕳️   ║
# ║  When I wrote this code, only I and God     ║
# ║  knew how it worked... now only God does.   ║
# ║  Don't waste your time here—just scroll on. ║
# ║  If you're still reading, bump the counters:║
# ║    hoursWasted += 1;                        ║
# ║    sanityLevel    -= 1;                     ║
# ╚═════════════════════════════════════════════╝

from flask import Flask
from config import Config
from extensions import init_extensions, db, jwt

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='static')
    app.config.from_object(config_class)

    # Initialize extensions
    init_extensions(app)

    # Register blueprints
    from routes import blueprints
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
