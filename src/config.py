import os


class BaseConfig:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", 5432)
    DB_NAME = os.getenv("DB_NAME", "tempdb")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", 1000))
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_EXPIRATION_SECONDS = os.getenv("JWT_TOKEN_EXPIRATION_SECONDS", 300)


class LocalConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    pass


CONFIG_BY_ENV = dict(local=LocalConfig, testing=TestingConfig, prod=ProdConfig)
