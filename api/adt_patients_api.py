"""
ADT Patients API Layer
Endpoints for managing and viewing ADT patient data
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from models.database import ADTPatient, SessionLocal
from sqlalchemy import desc

adt_patients_ns = Namespace('adt_patients', description='ADT Patient management operations')

# Response models
adt_patient_model = adt_patients_ns.model('ADTPatient', {
    'patient_id': fields.String(description='Patient ID (format: P000001)'),
    'id': fields.Integer(description='Numeric Patient ID (for internal use)'),
    'name': fields.String(description='Patient name'),
    'phone_number': fields.String(description='Patient phone number'),
    'hospital': fields.String(description='Hospital name'),
    'admission_date': fields.String(description='Admission date'),
    'discharge_date': fields.String(description='Discharge date'),
    'status': fields.String(description='Patient status (Admitted/Discharged)'),
    'discharge_summary': fields.Raw(description='Discharge summary JSON'),
    'created_at': fields.String(description='Record creation timestamp'),
})

adt_patients_list_model = adt_patients_ns.model('ADTPatientsList', {
    'total': fields.Integer(description='Total number of ADT patients'),
    'patients': fields.List(fields.Nested(adt_patient_model))
})


@adt_patients_ns.route('')
class ADTPatientsList(Resource):
    @adt_patients_ns.doc('get_adt_patients')
    @adt_patients_ns.response(200, 'Success', adt_patients_list_model)
    @adt_patients_ns.response(500, 'Internal Server Error')
    def get(self):
        """Get all ADT patients"""
        try:
            db = SessionLocal()
            try:
                patients = db.query(ADTPatient).order_by(desc(ADTPatient.created_at)).all()

                patients_data = []
                for patient in patients:
                    patients_data.append({
                        'patient_id': f'P{patient.id:06d}',  # Format as P000001
                        'id': patient.id,  # Keep numeric ID for internal use
                        'name': patient.name,
                        'phone_number': patient.phone_number,
                        'hospital': patient.hospital or '-',
                        'admission_date': patient.admission_date.isoformat() if patient.admission_date else None,
                        'discharge_date': patient.discharge_date.isoformat() if patient.discharge_date else None,
                        'status': patient.status or 'Unknown',
                        'discharge_summary': patient.discharge_summary,
                        'created_at': patient.created_at.isoformat() if patient.created_at else None,
                    })

                return {
                    'total': len(patients_data),
                    'patients': patients_data
                }, 200

            finally:
                db.close()

        except Exception as e:
            return {'error': f'Error fetching ADT patients: {str(e)}'}, 500
