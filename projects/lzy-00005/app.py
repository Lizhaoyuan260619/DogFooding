import os
from flask import Flask, render_template
from models.database import init_db, close_db
from blueprints.notes.routes import notes_bp
from blueprints.graph.routes import graph_bp
from blueprints.search.routes import search_bp
from blueprints.export.routes import export_bp

def create_app():
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zettelkasten.db')

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    app.register_blueprint(notes_bp, url_prefix='/api/notes')
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(export_bp, url_prefix='/api/export')

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
