from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Boolean, Text, ARRAY, DateTime, func, ForeignKey
import uuid


Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    guid: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    tg_id = Column(Text, nullable=True)
    tg_username = Column(Text, nullable=True)
    email = Column(Text, unique=True, nullable=True)
    password = Column(Text, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    roles = Column(ARRAY(Text), nullable=True, default=[])
    photo_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Tweet(Base):
    __tablename__ = 'tweets'

    guid: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message = Column(Text, nullable=False)
    created_by_guid = Column(ForeignKey("users.guid"))
    created_by = relationship("User", lazy="joined")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    is_deleted = Column(Boolean, nullable=False, default=False)
