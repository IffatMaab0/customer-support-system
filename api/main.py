import uuid

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from security import (
    verify_password,
    create_access_token,
    get_current_identity,
    get_current_staff,
    get_current_manager,
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



@app.post("/v1/auth/login", response_model=schemas.AuthResponse)
def login(
    data: schemas.LoginRequest,
    db: Session = Depends(get_db)
):


    customer = (
        db.query(models.Customer)
        .filter(models.Customer.email == data.email)
        .first()
    )

    if customer:
        if (
            not customer.is_active
            or not verify_password(
                data.password,
                customer.password_hash
            )
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_access_token(
            str(customer.id),
            "customer"
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "role": "customer",
            "name": customer.name,
            "email": customer.email
        }


    agent = (
        db.query(models.Agent)
        .filter(models.Agent.email == data.email)
        .first()
    )

    if not agent or not verify_password(
        data.password,
        agent.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    role = "manager" if agent.role == "admin" else agent.role

    token = create_access_token(
        str(agent.id),
        role
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": role,
        "name": agent.name,
        "email": agent.email
    }


@app.get("/v1/auth/me", response_model=schemas.MeResponse)
def get_me(
    current_user=Depends(get_current_identity)
):
    if isinstance(current_user, models.Agent):
        role = (
            "manager"
            if current_user.role == "admin"
            else current_user.role
        )
    else:
        role = "customer"

    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": role
    }


@app.post("/v1/auth/logout")
def logout():
    return {"message": "Logged out successfully"}



@app.post("/v1/tickets")
def create_ticket(
    data: schemas.TicketCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_identity)
):
    # Only customers can create support requests.
    if not isinstance(current_user, models.Customer):
        raise HTTPException(
            status_code=403,
            detail="Customer access required"
        )

    ticket = models.Ticket(
        id=uuid.uuid4(),

    
        customer_id=current_user.id,

        subject=data.subject,
        original_message=data.message,

        status="open",
        priority="normal",
        channel="web_form",

        assigned_agent_id=None
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket



@app.get("/v1/tickets")
def get_my_tickets(
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_identity)
):
    # Only customers can use the customer request list.
    if not isinstance(current_user, models.Customer):
        raise HTTPException(
            status_code=403,
            detail="Customer access required"
        )

    # Basic pagination protection.
    if page < 1:
        raise HTTPException(
            status_code=400,
            detail="Page must be at least 1"
        )

    if page_size < 1 or page_size > 10:
        raise HTTPException(
            status_code=400,
            detail="Page size must be between 1 and 10"
        )


    query = (
        db.query(models.Ticket)
        .filter(
            models.Ticket.customer_id == current_user.id
        )
    )


    if search:
        search = search.strip()

        query = query.filter(
            models.Ticket.subject.ilike(f"%{search}%")
            |
            models.Ticket.original_message.ilike(
                f"%{search}%"
            )
        )


    if status and status != "all":

        # UI says "in progress"
        # Database stores "in_progress"
        if status == "in progress":
            status = "in_progress"

        query = query.filter(
            models.Ticket.status == status
        )


    total = query.count()


    tickets = (
        query
        .order_by(models.Ticket.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "items": tickets,
        "total": total,
        "page": page,
        "page_size": page_size
    }



@app.get("/v1/meta")
def get_meta():
    return {
        "ticket_statuses": [
            "open",
            "in_progress",
            "resolved"
        ]
    }




@app.get("/tickets")
def list_tickets(
    status: str | None = None,
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    query = db.query(models.Ticket)

    if status:
        query = query.filter(
            models.Ticket.status == status
        )

    return (
        query
        .order_by(models.Ticket.created_at.desc())
        .all()
    )



@app.get("/tickets/stats")
def ticket_stats(
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    counts = {
        "total": db.query(models.Ticket).count()
    }

    for status in [
        "open",
        "in_progress",
        "resolved"
    ]:
        counts[status] = (
            db.query(models.Ticket)
            .filter(
                models.Ticket.status == status
            )
            .count()
        )

    return counts


@app.get("/tickets/available")
def available_tickets(
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Ticket)
        .filter(
            models.Ticket.status == "open",
            models.Ticket.assigned_agent_id.is_(None)
        )
        .order_by(models.Ticket.created_at.desc())
        .all()
    )


@app.patch("/tickets/{ticket_id}/claim")
def claim_ticket(
    ticket_id: uuid.UUID,
    claim: schemas.ClaimTicket,
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.assigned_agent_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Ticket is already assigned"
        )

    if claim.agent_id != current_agent.id:
        raise HTTPException(
            status_code=403,
            detail="You can only claim tickets for yourself"
        )

    ticket.assigned_agent_id = current_agent.id
    ticket.updated_at = func.now()

    db.commit()
    db.refresh(ticket)

    return ticket


@app.get("/tickets/my")
def my_tickets(
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Ticket)
        .filter(
            models.Ticket.assigned_agent_id == current_agent.id
        )
        .order_by(models.Ticket.created_at.desc())
        .all()
    )



@app.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: uuid.UUID,
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.assigned_agent_id != current_agent.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to access this ticket"
        )

    return ticket



@app.patch("/tickets/{ticket_id}/status")
def update_status(
    ticket_id: uuid.UUID,
    update: schemas.StatusUpdate,
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(models.Ticket)
        .filter(models.Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    if ticket.assigned_agent_id != current_agent.id:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to modify this ticket"
        )

    allowed_statuses = {
        "open",
        "in_progress",
        "resolved"
    }

    if update.status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid ticket status"
        )

    ticket.status = update.status
    ticket.updated_at = func.now()

    db.commit()
    db.refresh(ticket)

    return ticket


@app.get("/knowledge-base")
def list_docs(
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Doc)
        .order_by(models.Doc.created_at.desc())
        .all()
    )


@app.get("/agents")
def list_agents(
    current_agent=Depends(get_current_staff),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Agent)
        .order_by(models.Agent.name)
        .all()
    )


@app.get("/admin/agents")
def admin_agents(
    current_admin=Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Agent)
        .order_by(models.Agent.name)
        .all()
    )




@app.get("/admin/tickets")
def admin_tickets(
    current_admin=Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    tickets = (
        db.query(models.Ticket)
        .order_by(models.Ticket.created_at.desc())
        .all()
    )

    return [
        {
            "id": ticket.id,
            "subject": ticket.subject,
            "original_message": ticket.original_message,
            "status": ticket.status,
            "priority": ticket.priority,
            "channel": ticket.channel,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "customer_name": (
                ticket.customer.name
                if ticket.customer
                else None
            ),
            "customer_email": (
                ticket.customer.email
                if ticket.customer
                else None
            ),
            "agent_name": (
                ticket.assigned_agent.name
                if ticket.assigned_agent
                else None
            )
        }
        for ticket in tickets
    ]




@app.get("/admin/stats")
def admin_stats(
    current_admin=Depends(get_current_manager),
    db: Session = Depends(get_db)
):
    total_tickets = (
        db.query(models.Ticket).count()
    )

    open_tickets = (
        db.query(models.Ticket)
        .filter(models.Ticket.status == "open")
        .count()
    )

    in_progress_tickets = (
        db.query(models.Ticket)
        .filter(models.Ticket.status == "in_progress")
        .count()
    )

    resolved_tickets = (
        db.query(models.Ticket)
        .filter(models.Ticket.status == "resolved")
        .count()
    )

    total_agents = (
        db.query(models.Agent).count()
    )

    return {
        "total_tickets": total_tickets,
        "open": open_tickets,
        "in_progress": in_progress_tickets,
        "resolved": resolved_tickets,
        "total_agents": total_agents
    }