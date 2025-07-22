import os
from application import create_app, db
from flask_migrate import Migrate  # type: ignore

# Create the Flask app instance
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

# Optional: Define the shell context
def make_shell_context():
    return dict(app=app, db=db)

if __name__ == '__main__':
    # Added a condition to run the app only when needed
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))