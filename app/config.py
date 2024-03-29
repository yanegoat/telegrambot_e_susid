import os
import yaml
import logging.config
from app.enums import Environ


class ConfigProvider:
    def __init__(self):
        self.__env = Environ[os.environ.get('ENV', 'local')]

        dirname = os.path.dirname(__file__)
        filename = os.path.abspath(
            os.path.join(dirname, f'../config/config-{self.__env.name}.yaml'))
        with open(filename, 'r') as f:
            self.__cfg = yaml.load(f, Loader=yaml.SafeLoader)

        filename = os.path.abspath(
            os.path.join(dirname, '../config/logging.conf'))
        logging.config.fileConfig(filename, disable_existing_loggers=False)

    @property
    def env(self) -> Environ:
        return self.__env

    @property
    def db_port(self) -> int:
        default = self.__cfg['db']['port']

        if self.__env == Environ.local:
            return int(os.getenv("POSTGRES_PORT", default))

        return int(os.getenv("ENGAGE_DB_PORT", default))

    @property
    def db_name(self) -> str:
        default = self.__cfg['db']['name']

        if self.__env == Environ.local:
            return os.getenv("POSTGRES_DB", default)

        return os.getenv("ENGAGE_DB_NAME", default)

    @property
    def vault_secrets(self) -> dict:
        secrets = {
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "pass": os.getenv("POSTGRES_PASSWORD", "admin"),
            "host": os.getenv("POSTGRES_HOST", "localhost"),
        }
        return secrets

    @property
    def bot_token(self) -> str:
        return self.__cfg['telegram']['token']

config = ConfigProvider()


class PostgresConfig:
    PORT = config.db_port
    DATABASE = config.db_name
    SECRETS = config.vault_secrets
    HOST = SECRETS['host']
    URL = f"postgresql+asyncpg://{SECRETS['user']}:{SECRETS['pass']}@{HOST}:{PORT}/{DATABASE}"
    ECHO = int(os.getenv("DB_ECHO", 0))


logger = logging.getLogger(__name__)
db_secrets = (PostgresConfig.SECRETS["user"] is not None) and \
             (PostgresConfig.SECRETS["pass"] is not None) and \
             (PostgresConfig.SECRETS["host"] is not None)
logger.info(f"DB host: [{PostgresConfig.HOST}]")
logger.info(f"DB port: [{PostgresConfig.PORT}]")
logger.info(f"DB name: [{PostgresConfig.DATABASE}]")
logger.info(f"DB secrets available: [{db_secrets}]")
