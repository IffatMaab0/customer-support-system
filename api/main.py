import uuid
from sqlalchemy import func
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

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


@app.get("/tickets", response_model=list[schemas.TicketOut])
def list_tickets(
    status: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Ticket)

    if status:
        query = query.filter(models.Ticket.status == status)

    return query.order_by(models.Ticket.created_at.desc()).all()

@app.get("/tickets/stats")
def ticket_stats(db: Session = Depends(get_db)):
    counts = {"total": db.query(models.Ticket).count()}

    for status in ["open", "pending", "resolved", "escalated"]:
        counts[status] = (
            db.query(models.Ticket)
            .filter_by(status=status)
            .count()
        )

    return counts

@app.get("/tickets/{ticket_id}", response_model=schemas.TicketOut)
def get_ticket(
    ticket_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    ticket = db.query(models.Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return ticket


@app.patch("/tickets/{ticket_id}/status", response_model=schemas.TicketOut)
def update_status(
    ticket_id: uuid.UUID,
    update: schemas.StatusUpdate,
    db: Session = Depends(get_db)
):
    ticket = db.query(models.Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = update.status
    ticket.updated_at = func.now()

    db.commit()
    db.refresh(ticket)

    return ticket


@app.patch("/tickets/{ticket_id}/response", response_model=schemas.TicketOut)
def add_response(
    ticket_id: uuid.UUID,
    update: schemas.ResponseUpdate,
    db: Session = Depends(get_db)
):
    ticket = db.query(models.Ticket).filter_by(id=ticket_id).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.response = update.response
    ticket.responded_at = func.now()
    ticket.updated_at = func.now()

    db.commit()
    db.refresh(ticket)

    return ticket

@app.get("/knowledge-base", response_model=list[schemas.DocOut])
def list_docs(db: Session = Depends(get_db)):
    return db.query(models.Doc).all()

