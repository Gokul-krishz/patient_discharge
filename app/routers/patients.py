from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import PatientCreate, PatientResponse, CareTeamMemberCreate, CareTeamMemberResponse
from app.models import Patient, CareTeamMember, PatientCareTeam
from typing import List

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.post("/", response_model=PatientResponse)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new patient record.
    """
    # Check if patient_id already exists
    existing = db.query(Patient).filter(Patient.patient_id == patient.patient_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient ID already exists")
    
    # Create patient
    db_patient = Patient(
        patient_id=patient.patient_id,
        phone_number=patient.phone_number,
        name=patient.name,
        medical_context=patient.medical_context
    )
    db.add(db_patient)
    db.flush()
    
    # Add care team members if provided
    if patient.care_team_member_ids:
        for member_id in patient.care_team_member_ids:
            member = db.query(CareTeamMember).filter(CareTeamMember.id == member_id).first()
            if member:
                association = PatientCareTeam(
                    patient_id=db_patient.id,
                    care_team_member_id=member.id
                )
                db.add(association)
    
    db.commit()
    db.refresh(db_patient)
    return db_patient


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a patient by their patient_id.
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/", response_model=List[PatientResponse])
def list_patients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all patients with pagination.
    """
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients


@router.post("/care-team/", response_model=CareTeamMemberResponse)
def create_care_team_member(
    member: CareTeamMemberCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new care team member.
    """
    db_member = CareTeamMember(
        name=member.name,
        email=member.email,
        role=member.role
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member


@router.get("/care-team/", response_model=List[CareTeamMemberResponse])
def list_care_team_members(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List all care team members.
    """
    members = db.query(CareTeamMember).offset(skip).limit(limit).all()
    return members
