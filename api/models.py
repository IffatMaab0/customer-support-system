from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
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
    role = Column(String, nullable=False, default="agent")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True)

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False
    )

    assigned_agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True
    )

    subject = Column(String(160), nullable=False)
    original_message = Column(Text, nullable=False)

    status = Column(
        String,
        nullable=False,
        default="open"
    )

    priority = Column(
        String,
        nullable=False,
        default="normal"
    )

    channel = Column(
        String,
        nullable=False,
        default="web_form"
    )

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default="now()"
    )

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default="now()"
    )

    customer = relationship("Customer")
    assigned_agent = relationship("Agent")


class Doc(Base):
    __tablename__ = "docs"

    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default="now()"
    )