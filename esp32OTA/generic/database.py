# Framework Imports
from flask_mongoengine import MongoEngine
db = MongoEngine()


def initialize_db(app):
    return db.init_app(app)
