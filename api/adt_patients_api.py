"""
ADT Patients API Layer
Endpoints for managing and viewing ADT patient data
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from models.database import ADTPatient, SessionLocal
from sqlalchemy import desc
from datetime import datetime

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
    'care_team': fields.Integer(description='Care team member ID'),
    'created_at': fields.String(description='Record creation timestamp'),
})

# Request model for creating new ADT patient
create_adt_patient_model = adt_patients_ns.model('CreateADTPatient', {
    'patient_name': fields.String(required=True, description='Patient name'),
    'mobile_number': fields.String(required=True, description='Patient mobile number'),
    'hospital': fields.String(required=True, description='Hospital name or ID'),
    'description': fields.String(required=True, description='Patient description/notes'),
    'care_team': fields.Integer(description='Care team member ID')
})

adt_patients_list_model = adt_patients_ns.model('ADTPatientsList', {
    'total': fields.Integer(description='Total number of ADT patients'),
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page'),
    'total_pages': fields.Integer(description='Total number of pages'),
    'patients': fields.List(fields.Nested(adt_patient_model))
})


@adt_patients_ns.route('')
class ADTPatientsList(Resource):
    @adt_patients_ns.doc('create_adt_patient')
    @adt_patients_ns.expect(create_adt_patient_model)
    @adt_patients_ns.response(201, 'Patient created successfully', adt_patient_model)
    @adt_patients_ns.response(400, 'Bad Request')
    @adt_patients_ns.response(500, 'Internal Server Error')
    def post(self):
        """Create a new ADT patient record"""
        try:
            data = request.json
            
            patient_name = data.get('patient_name')
            mobile_number = data.get('mobile_number')
            hospital = data.get('hospital')
            description = data.get('description')
            care_team = data.get('care_team')
            
            if not patient_name or not mobile_number or not hospital or not description:
                return {'error': 'Missing required fields: patient_name, mobile_number, hospital, description'}, 400
            
            db = SessionLocal()
            try:
                existing_patient = db.query(ADTPatient).filter_by(phone_number=mobile_number).first()
                if existing_patient:
                    return {'error': f'Patient with phone number {mobile_number} already exists'}, 400
                
                new_patient = ADTPatient(
                    name=patient_name,
                    phone_number=mobile_number,
                    hospital=hospital,
                    admission_date=datetime.utcnow(),
                    status='Admitted',
                    discharge_summary={'description': description},
                    care_team=care_team
                )
                
                db.add(new_patient)
                db.commit()
                db.refresh(new_patient)
                
                return {
                    'patient_id': f'P{new_patient.id:06d}',
                    'id': new_patient.id,
                    'name': new_patient.name,
                    'phone_number': new_patient.phone_number,
                    'hospital': new_patient.hospital,
                    'admission_date': new_patient.admission_date.isoformat(),
                    'discharge_date': None,
                    'status': new_patient.status,
                    'discharge_summary': new_patient.discharge_summary,
                    'care_team': new_patient.care_team,
                    'created_at': new_patient.created_at.isoformat(),
                    'message': 'Patient created successfully'
                }, 201
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error creating ADT patient: {str(e)}'}, 500
    
    @adt_patients_ns.doc('get_adt_patients')
    @adt_patients_ns.param('page', 'Page number (default: 1)', type=int)
    @adt_patients_ns.param('per_page', 'Items per page (default: 10, max: 100)', type=int)
    @adt_patients_ns.param('search', 'Search by patient name or patient ID (e.g. P000001)', type=str)
    @adt_patients_ns.param('hospital', 'Filter by hospital name', type=str)
    @adt_patients_ns.param('status', 'Filter by status (Admitted/Discharged)', type=str)
    @adt_patients_ns.response(200, 'Success', adt_patients_list_model)
    @adt_patients_ns.response(400, 'Bad Request')
    @adt_patients_ns.response(500, 'Internal Server Error')
    def get(self):
        """Get ADT patients with search, filter, and pagination"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            search_query = request.args.get('search', None, type=str)
            hospital_filter = request.args.get('hospital', None, type=str)
            status_filter = request.args.get('status', None, type=str)

            if page < 1:
                return {'error': 'Page number must be >= 1'}, 400
            if per_page < 1 or per_page > 100:
                return {'error': 'per_page must be between 1 and 100'}, 400

            db = SessionLocal()
            try:
                query = db.query(ADTPatient).order_by(desc(ADTPatient.created_at))

                # Search by patient name or ID (e.g. P000001)
                if search_query:
                    search_query = search_query.strip()
                    if search_query.upper().startswith('P') and search_query[1:].isdigit():
                        query = query.filter(ADTPatient.id == int(search_query[1:]))
                    else:
                        query = query.filter(ADTPatient.name.ilike(f'%{search_query}%'))

                # Filter by hospital
                if hospital_filter:
                    query = query.filter(ADTPatient.hospital == hospital_filter)

                # Filter by status
                if status_filter:
                    query = query.filter(ADTPatient.status == status_filter)

                total = query.count()
                total_pages = (total + per_page - 1) // per_page
                offset = (page - 1) * per_page
                patients = query.offset(offset).limit(per_page).all()

                patients_data = []
                for patient in patients:
                    patients_data.append({
                        'patient_id': f'P{patient.id:06d}',
                        'id': patient.id,
                        'name': patient.name,
                        'phone_number': patient.phone_number,
                        'hospital': patient.hospital or '-',
                        'admission_date': patient.admission_date.isoformat() if patient.admission_date else None,
                        'discharge_date': patient.discharge_date.isoformat() if patient.discharge_date else None,
                        'status': patient.status or 'Unknown',
                        'discharge_summary': patient.discharge_summary,
                        'care_team': patient.care_team,
                        'created_at': patient.created_at.isoformat() if patient.created_at else None,
                    })

                return {
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'patients': patients_data
                }, 200

            finally:
                db.close()

        except Exception as e:
            return {'error': f'Error fetching ADT patients: {str(e)}'}, 500


@adt_patients_ns.route('/hospitals')
class ADTHospitalsList(Resource):
    @adt_patients_ns.doc('get_adt_hospitals')
    @adt_patients_ns.response(200, 'Success')
    @adt_patients_ns.response(500, 'Internal Server Error')
    def get(self):
        """Get all hospitals from hospitals table"""
        try:
            from models.database import Hospital
            
            db = SessionLocal()
            try:
                hospitals = db.query(Hospital).order_by(Hospital.name).all()

                hospital_list = []
                for hospital in hospitals:
                    hospital_list.append({
                        'id': hospital.id,
                        'name': hospital.name
                    })

                return {
                    'hospitals': hospital_list,
                    'count': len(hospital_list)
                }, 200

            finally:
                db.close()

        except Exception as e:
            return {'error': f'Error fetching hospitals: {str(e)}'}, 500
