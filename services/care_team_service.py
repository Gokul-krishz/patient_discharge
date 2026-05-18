"""
Care Team Service
Manages care team members assigned to patients
"""
from typing import Dict, Any, List, Optional
from models.database import CareTeamMember, Patient, SessionLocal
from datetime import datetime


class CareTeamService:
    """Service for managing patient care team members"""
    
    def _get_db(self):
        """Get database session"""
        return SessionLocal()
    
    def add_care_team_member(
        self,
        patient_id: int,
        name: str,
        role: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        specialty: Optional[str] = None,
        is_primary: bool = False,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a care team member to a patient
        
        Args:
            patient_id: ID of the patient
            name: Name of the care team member
            role: Role (e.g., 'Nephrologist', 'Nurse', 'Dietitian')
            phone_number: Contact phone number
            email: Contact email
            specialty: Medical specialty
            is_primary: Whether this is the primary care team member
            notes: Additional notes
            
        Returns:
            Dictionary with care team member details
        """
        db = self._get_db()
        try:
            # Verify patient exists
            patient = db.query(Patient).filter_by(id=patient_id).first()
            if not patient:
                raise ValueError(f"Patient with ID {patient_id} not found")
            
            # Create care team member
            member = CareTeamMember(
                patient_id=patient_id,
                name=name,
                role=role,
                phone_number=phone_number,
                email=email,
                specialty=specialty,
                is_primary=is_primary,
                notes=notes
            )
            
            db.add(member)
            db.commit()
            db.refresh(member)
            
            return {
                'success': True,
                'member_id': member.id,
                'patient_id': member.patient_id,
                'name': member.name,
                'role': member.role,
                'phone_number': member.phone_number,
                'email': member.email,
                'specialty': member.specialty,
                'is_primary': member.is_primary,
                'notes': member.notes,
                'created_at': member.created_at.isoformat()
            }
        finally:
            db.close()
    
    def get_care_team_by_patient(self, patient_id: int) -> List[Dict[str, Any]]:
        """
        Get all care team members for a patient
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            List of care team member dictionaries
        """
        db = self._get_db()
        try:
            members = (
                db.query(CareTeamMember)
                .filter_by(patient_id=patient_id)
                .order_by(CareTeamMember.is_primary.desc(), CareTeamMember.created_at)
                .all()
            )
            
            return [{
                'id': m.id,
                'patient_id': m.patient_id,
                'name': m.name,
                'role': m.role,
                'phone_number': m.phone_number,
                'email': m.email,
                'specialty': m.specialty,
                'is_primary': m.is_primary,
                'notes': m.notes,
                'created_at': m.created_at.isoformat(),
                'updated_at': m.updated_at.isoformat()
            } for m in members]
        finally:
            db.close()
    
    def update_care_team_member(
        self,
        member_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update a care team member's information
        
        Args:
            member_id: ID of the care team member
            **kwargs: Fields to update (name, role, phone_number, email, specialty, is_primary, notes)
            
        Returns:
            Dictionary with updated care team member details
        """
        db = self._get_db()
        try:
            member = db.query(CareTeamMember).filter_by(id=member_id).first()
            if not member:
                raise ValueError(f"Care team member with ID {member_id} not found")
            
            # Update allowed fields
            allowed_fields = ['name', 'role', 'phone_number', 'email', 'specialty', 'is_primary', 'notes']
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    setattr(member, field, value)
            
            member.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(member)
            
            return {
                'success': True,
                'member_id': member.id,
                'patient_id': member.patient_id,
                'name': member.name,
                'role': member.role,
                'phone_number': member.phone_number,
                'email': member.email,
                'specialty': member.specialty,
                'is_primary': member.is_primary,
                'notes': member.notes,
                'updated_at': member.updated_at.isoformat()
            }
        finally:
            db.close()
    
    def delete_care_team_member(self, member_id: int) -> Dict[str, Any]:
        """
        Delete a care team member
        
        Args:
            member_id: ID of the care team member
            
        Returns:
            Dictionary with success status
        """
        db = self._get_db()
        try:
            member = db.query(CareTeamMember).filter_by(id=member_id).first()
            if not member:
                raise ValueError(f"Care team member with ID {member_id} not found")
            
            db.delete(member)
            db.commit()
            
            return {
                'success': True,
                'message': f'Care team member {member_id} deleted successfully'
            }
        finally:
            db.close()
    
    def get_primary_care_member(self, patient_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the primary care team member for a patient
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Dictionary with primary care team member details or None
        """
        db = self._get_db()
        try:
            member = (
                db.query(CareTeamMember)
                .filter_by(patient_id=patient_id, is_primary=True)
                .first()
            )
            
            if not member:
                return None
            
            return {
                'id': member.id,
                'patient_id': member.patient_id,
                'name': member.name,
                'role': member.role,
                'phone_number': member.phone_number,
                'email': member.email,
                'specialty': member.specialty,
                'is_primary': member.is_primary,
                'notes': member.notes,
                'created_at': member.created_at.isoformat(),
                'updated_at': member.updated_at.isoformat()
            }
        finally:
            db.close()
