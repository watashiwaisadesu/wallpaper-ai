import logging
from app.db.models.log import LogEntry
from sqlalchemy.orm import sessionmaker
from app.core import settings_env

from sqlalchemy import create_engine



sync_engine = create_engine(settings_env.DB_URL_SYNC, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine)

def add_log_to_db_sync(log_level: str, message: str, source: str):
    # Create a new session for each log entry
    session = SyncSessionLocal()
    try:
        log_entry = LogEntry(log_level=log_level, message=message, source=source)
        session.add(log_entry)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()  # Close the session to avoid leakage

class SyncDatabaseHandler(logging.Handler):
    def emit(self, record):
        if record.name.startswith('sqlalchemy') or record.name.startswith('passlib'):
            return

        log_entry = self.format(record)
        add_log_to_db_sync(record.levelname, log_entry, record.name)

def setup_logging():
    db_handler = SyncDatabaseHandler()
    logging.getLogger().addHandler(db_handler)
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().info("Application started")


