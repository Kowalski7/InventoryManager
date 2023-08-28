from flask import Flask
from werkzeug.security import generate_password_hash
import atexit
import json
import os
import random
import string

import app.extensions as extensions

from app.middleware.exceptionHandler import handle_exception
from app.utils import safe_uuid
from app.models.Users import Users
from app.modules.scheduled_tasks import TaskScheduler
from app.routes.account import account
from app.routes.authentication import authentication
from app.routes.inventory import inventory
from app.routes.images import inv_images
from app.routes.price_changes import price_changes
from app.routes.suggestions import suggestions
from app.routes.product_lookup import product_lookup
from app.routes.configurator import configurator
from app.routes.archive import archive
from app.routes.statistics import statistics
from app.routes.tests import tests
from config import Config


def on_server_shutdown():
    extensions.task_scheduler.stop()


def create_default_config():
    data = {
        "threshold_restock_days": 7,
        "threshold_price_increase": 0.7,
        "threshold_price_decrease": -0.4,
        "multiplier_price_increase": 0.12,
        "multiplier_price_decrease": 0.2,
        "scheduled_tasks": {
            "auto_suggestions": "02:00",
            "auto_cleanup": "03:00"
        }
    }
    with open("config.json", "w") as config_file:
        config_file.write(json.dumps(data))


def create_default_manager_account():
    random_password = ''.join(random.choices(
        string.ascii_letters + string.digits, k=12))
    manager = Users(
        public_id=safe_uuid(),
        name="Default Manager Account",
        username="manager",
        password=generate_password_hash(random_password, method='scrypt'),
        roles=["ROLE_EMPLOYEE", "ROLE_MANAGER"]
    )

    extensions.db.session.add(manager)
    extensions.db.session.commit()

    print(
        f"No user account was found in the database. A default manager account has been created with the following credentials:\n\n\tUsername: manager\n\tPassword: {random_password}\n\nPlease change the password immediately after logging in.")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions here
    extensions.db.init_app(app)

    # Create default config if it doesn't exist
    if not os.path.exists("config.json"):
        create_default_config()

    # Load configuration file
    with open("config.json", "r") as config_file:
        Config.CONFIG_DATA = json.load(config_file)

    with app.app_context() as ctx:
        # Create database tables
        from app.models.Users import Users
        from app.models.Inventory import Inventory
        from app.models.Transactions import Transactions
        from app.models.PurchasedProducts import PurchasedProducts
        from app.models.SuggestedModifications import SuggestedModifications
        from app.models.ArchivedInventory import ArchivedInventory

        extensions.db.create_all()
        extensions.db.session.commit()

        # Create default manager account if it doesn't exist
        if Users.query.filter(Users.roles.like("%ROLE_MANAGER%")).count() == 0:
            create_default_manager_account()

        # Create and start task scheduler
        extensions.task_scheduler = TaskScheduler()
        extensions.task_scheduler.start()

    # Register exit handler
    atexit.register(on_server_shutdown)

    # Register blueprints here
    app.register_blueprint(authentication)
    app.register_blueprint(account)
    app.register_blueprint(inventory)
    app.register_blueprint(inv_images)
    app.register_blueprint(statistics)
    app.register_blueprint(suggestions)
    app.register_blueprint(price_changes)
    app.register_blueprint(product_lookup)
    app.register_blueprint(configurator)
    app.register_blueprint(archive)
    app.register_blueprint(tests)

    # Register error handler
    app.register_error_handler(Exception, handle_exception)

    return app
