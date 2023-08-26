import dotenv

# dotenv_data = dotenv.dotenv_values(".env")
dotenv_data = dotenv.dotenv_values(".env.dev")  # for development only


class Config:
    INTERNAL_NUMBER = 7
    MOBILE_APP_BUILD = 10
    BASE_URL = dotenv_data["BASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    UPLOAD_FOLDER = "static/inventory_images/"
    SECRET_KEY = dotenv_data["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = dotenv_data["SQLALCHEMY_DATABASE_URI"]
