from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models.user_model import User, UserCreate

# Enable pool_pre_ping to avoid using stale / closed connections from the
# connection pool. Add a small connect timeout so initial network/connect
# attempts fail fast instead of hanging indefinitely. Tune pool_size and
# max_overflow to reasonable defaults for local deployments — adjust for
# production as needed.
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    # connect_args passed to the DB driver (psycopg). Keepalives help detect
    # and recover from broken TCP connections (common in cloud networks).
    connect_args={
        "connect_timeout": 10,
        # Enable TCP keepalives (supported by libpq/psycopg) so dead sockets are
        # detected sooner. Values are seconds.
        "keepalives": 1,
        "keepalives_idle": 60,
        "keepalives_interval": 15,
        "keepalives_count": 5,
    },
    # Wait up to 30s for a connection from the pool before raising
    pool_timeout=30,
)


# make sure all SQLModel models are imported ( models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # from  core.engine import engine
    # This works because the models are already imported and registered from  models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password="admin123",  # Short password for initial setup
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)
