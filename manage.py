import os
from application import create_app, db

from flask_migrate import Migrate   # type: ignore
app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)
def make_shell_context():
    return dict(app=app, db=db)

if __name__ == '__main__':
    app.run(host='localhost', port=8080 )

