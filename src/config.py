import os


class BaseConfig:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", 5432)
    DB_NAME = os.getenv("DB_NAME", "tempdb")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")
    ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", 1000))
    JWT_SECRET_KEY = "4f7dad0650214bd59a2a8d778d447f4b"


class LocalConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    pass


CONFIG_BY_ENV = dict(local=LocalConfig, testing=TestingConfig, prod=ProdConfig)
