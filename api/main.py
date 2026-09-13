
import uuid

from sqlalchemy import func
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from security import (
    verify_password,
    create_access_token,
    get_current_agent
)

import models
import schemas
from database import get_db


app = FastAPI(title="Support Ticket API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}



@app.post("/tickets", response_model=schemas.TicketOut)
def create_ticket(
    ticket: schemas.TicketCreate,
    db: Session = Depends(get_db)
):
    customer = (
        db.query(models.Customer)
        .filter_by(email=ticket.customer_email)
        .first()
    )

    if not customer:
        customer = models.Customer(
            id=uuid.uuid4(),
            name=ticket.customer_name,
            email=ticket.customer_email,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

    new_ticket = models.Ticket(
        id=uuid.uuid4(),
        customer_id=customer.id,
        subject=ticket.subject,
        message=ticket.message,
        status="open",
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return new_ticket



@app.post("/login")
def login(
    data: schemas.AgentLogin,
    db: Session = Depends(get_db)
):
    agent = (
        db.query(models.Agent)
        .filter(models.Agent.email == data.email)
        .first()
    )

    if not agent:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        data.password,
        agent.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        str(agent.id)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "agent_id": str(agent.id),
        "name": agent.name,
        "email": agent.email
    }



@app.get("/tickets", response_model=list[schemas.TicketOut])
def list_tickets(
    status: str | None = None,
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    query = db.query(models.Ticket)

    if status:
        query = query.filter(models.Ticket.status == status)

    return (
        query
        .order_by(models.Ticket.created_at.desc())
        .all()
    )


@app.get("/tickets/stats")
def ticket_stats(
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    counts = {
        "total": db.query(models.Ticket).count()
    }

    for status in [
        "open",
        "pending",
        "resolved",
        "escalated"
    ]:
        counts[status] = (
            db.query(models.Ticket)
            .filter_by(status=status)
            .count()
        )

    return counts


@app.get(
    "/tickets/available",
    response_model=list[schemas.TicketOut]
)
def available_tickets(
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Ticket)
        .filter(
            models.Ticket.status == "open",
            models.Ticket.agent_id.is_(None)
        )
        .order_by(models.Ticket.created_at.desc())
        .all()
    )


@app.patch(
    "/tickets/{ticket_id}/claim",
    response_model=schemas.TicketOut
)
def claim_ticket(
    ticket_id: uuid.UUID,
    claim: schemas.ClaimTicket,
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(models.Ticket)
        .filter_by(id=ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.agent_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Ticket is already assigned"
        )

    if claim.agent_id != current_agent.id:
        raise HTTPException(
            status_code=403,
            detail="You can only claim tickets for yourself"
        )

    ticket.agent_id = current_agent.id
    ticket.updated_at = func.now()

    db.commit()
    db.refresh(ticket)

    return ticket


@app.get(
    "/tickets/my",
    response_model=list[schemas.TicketOut]
)
def my_tickets(
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Ticket)
        .filter(
            models.Ticket.agent_id == current_agent.id
        )
        .order_by(models.Ticket.created_at.desc())
        .all()
    )


@app.get(
    "/tickets/{ticket_id}",
    response_model=schemas.TicketOut
)
def get_ticket(
    ticket_id: uuid.UUID,
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(models.Ticket)
        .filter_by(id=ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.agent_id != current_agent.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this ticket"
        )

    return ticket


@app.patch(
    "/tickets/{ticket_id}/status",
    response_model=schemas.TicketOut
)
def update_status(
    ticket_id: uuid.UUID,
    update: schemas.StatusUpdate,
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(models.Ticket)
        .filter_by(id=ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.agent_id != current_agent.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to modify this ticket"
        )

    ticket.status = update.status
    ticket.updated_at = func.now()

    db.commit()
    db.refresh(ticket)

    return ticket


@app.patch(
    "/tickets/{ticket_id}/response",
    response_model=schemas.TicketOut
)
def add_response(
    ticket_id: uuid.UUID,
    update: schemas.ResponseUpdate,
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(models.Ticket)
        .filter_by(id=ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.agent_id != current_agent.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to modify this ticket"
        )

    ticket.response = update.response
    ticket.responded_at = func.now()
    ticket.updated_at = func.now()

    db.commit()
    db.refresh(ticket)

    return ticket




@app.get(
    "/knowledge-base",
    response_model=list[schemas.DocOut]
)
def list_docs(
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    return db.query(models.Doc).all()



@app.get(
    "/agents",
    response_model=list[schemas.AgentOut]
)
def list_agents(
    current_agent: models.Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Agent)
        .order_by(models.Agent.name)
        .all()
    )


