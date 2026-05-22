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
    'page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page'),
    'total_pages': fields.Integer(description='Total number of pages'),
    'patients': fields.List(fields.Nested(adt_patient_model))
})


@adt_patients_ns.route('')
class ADTPatientsList(Resource):
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
        """Get all unique hospitals from ADT patients"""
        try:
            db = SessionLocal()
            try:
                hospitals = (
                    db.query(ADTPatient.hospital)
                    .filter(ADTPatient.hospital.isnot(None))
                    .distinct()
                    .order_by(ADTPatient.hospital)
                    .all()
                )

                hospital_list = [h[0] for h in hospitals if h[0]]

                return {
                    'hospitals': hospital_list,
                    'count': len(hospital_list)
                }, 200

            finally:
                db.close()

        except Exception as e:
            return {'error': f'Error fetching ADT hospitals: {str(e)}'}, 500
