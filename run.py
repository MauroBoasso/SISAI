from app import app
from app.config import DevelopmentConfig
if __name__ == '__main__':
    app.config.from_object(DevelopmentConfig)
    app.run(host="localhost", port=9566)