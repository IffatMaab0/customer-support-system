from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    
    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default="now()"
    )


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True)

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False
    )

    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True
    )
    customer = relationship("Customer")

    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    response = Column(Text, nullable=True)
    responded_at = Column(TIMESTAMP(timezone=True), nullable=True)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default="now()"
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default="now()"
    )


class Doc(Base):
    __tablename__ = "docs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default="now()"
    )