def create_app(config_name='dev'):
    app = Flask(__name__)

    app.config.from_object(config_by_name[config_name])

    # Force the secret key AFTER loading config
    app.config['SECRET_KEY'] = 'test-secret-key-123'
    app.secret_key = 'test-secret-key-123'

    print("SECRET_KEY =", app.config.get("SECRET_KEY"))
    print("app.secret_key =", app.secret_key)

    db.init_app(app)