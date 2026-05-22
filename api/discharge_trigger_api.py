"""
Discharge Trigger API
Allows external systems to trigger patient discharge and automatically send SMS
"""
from flask import request
from flask_restx import Namespace, Resource, fields
from models.database import Patient, SessionLocal
from datetime import datetime

discharge_ns = Namespace('discharge', description='Discharge trigger operations')

# Request models
discharge_trigger_model = discharge_ns.model('DischargeTrigger', {
    'patient_name': fields.String(required=True, description='Patient name'),
    'phone_number': fields.String(required=True, description='Patient phone number (E.164 format)'),
    'hospital': fields.String(required=False, description='Hospital name'),
    'admission_date': fields.String(required=False, description='Admission date (YYYY-MM-DD)'),
    'discharge_date': fields.String(required=False, description='Discharge date (YYYY-MM-DD)'),
})

update_status_model = discharge_ns.model('UpdateStatus', {
    'patient_id': fields.String(required=True, description='Patient ID (e.g., P000001)'),
    'status': fields.String(required=True, description='New status (Admitted/Discharged)'),
})


@discharge_ns.route('/trigger')
class DischargeTrigger(Resource):
    @discharge_ns.doc('trigger_discharge')
    @discharge_ns.expect(discharge_trigger_model)
    @discharge_ns.response(201, 'Patient discharged and SMS triggered')
    @discharge_ns.response(400, 'Bad Request')
    @discharge_ns.response(500, 'Internal Server Error')
    def post(self):
        """
        Trigger patient discharge - Creates/updates patient and automatically sends SMS
        
        This endpoint:
        1. Creates new patient or updates existing patient
        2. Sets status to 'Discharged'
        3. Database trigger automatically sends SMS via listener
        """
        try:
            data = request.json
            
            # Validate required fields
            name = data.get('patient_name', '').strip()
            phone = data.get('phone_number', '').strip()
            
            if not name or not phone:
                return {'error': 'patient_name and phone_number are required'}, 400
            
            # Parse dates
            admission_date = None
            discharge_date = None
            
            if data.get('admission_date'):
                try:
                    admission_date = datetime.strptime(data['admission_date'], '%Y-%m-%d')
                except ValueError:
                    return {'error': 'Invalid admission_date format. Use YYYY-MM-DD'}, 400
            
            if data.get('discharge_date'):
                try:
                    discharge_date = datetime.strptime(data['discharge_date'], '%Y-%m-%d')
                except ValueError:
                    return {'error': 'Invalid discharge_date format. Use YYYY-MM-DD'}, 400
            else:
                # Default to today if not provided
                discharge_date = datetime.now()
            
            db = SessionLocal()
            try:
                # Check if patient already exists
                existing_patient = db.query(Patient).filter_by(phone_number=phone).first()
                
                if existing_patient:
                    # Update existing patient
                    existing_patient.name = name
                    existing_patient.hospital = data.get('hospital', existing_patient.hospital)
                    existing_patient.admission_date = admission_date or existing_patient.admission_date
                    existing_patient.discharge_date = discharge_date
                    existing_patient.status = 'Discharged'
                    existing_patient.follow_up = 'Pending'  # Reset follow-up status
                    
                    db.commit()
                    db.refresh(existing_patient)
                    
                    patient_id = f'P{str(existing_patient.id).zfill(6)}'
                    action = 'updated'
                else:
                    # Create new patient
                    new_patient = Patient(
                        name=name,
                        phone_number=phone,
                        hospital=data.get('hospital'),
                        admission_date=admission_date,
                        discharge_date=discharge_date,
                        status='Discharged',
                        follow_up='Pending'
                    )
                    
                    db.add(new_patient)
                    db.commit()
                    db.refresh(new_patient)
                    
                    patient_id = f'P{str(new_patient.id).zfill(6)}'
                    action = 'created'
                
                return {
                    'success': True,
                    'message': f'Patient {action} and discharge triggered',
                    'patient_id': patient_id,
                    'patient_name': name,
                    'phone_number': phone,
                    'status': 'Discharged',
                    'follow_up': 'Pending',
                    'note': 'SMS will be sent automatically by the listener'
                }, 201
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error triggering discharge: {str(e)}'}, 500


@discharge_ns.route('/update-status')
class UpdatePatientStatus(Resource):
    @discharge_ns.doc('update_patient_status')
    @discharge_ns.expect(update_status_model)
    @discharge_ns.response(200, 'Status updated successfully')
    @discharge_ns.response(404, 'Patient not found')
    @discharge_ns.response(500, 'Internal Server Error')
    def post(self):
        """
        Update patient status (Admitted/Discharged)
        
        If status changes to 'Discharged', SMS will be automatically sent
        """
        try:
            data = request.json
            patient_id_str = data.get('patient_id', '')
            new_status = data.get('status', '')
            
            if not patient_id_str or not new_status:
                return {'error': 'patient_id and status are required'}, 400
            
            if new_status not in ['Admitted', 'Discharged']:
                return {'error': 'status must be either "Admitted" or "Discharged"'}, 400
            
            # Extract numeric ID
            try:
                numeric_id = int(patient_id_str.replace('P', ''))
            except ValueError:
                return {'error': 'Invalid patient_id format'}, 400
            
            db = SessionLocal()
            try:
                patient = db.query(Patient).filter(Patient.id == numeric_id).first()
                
                if not patient:
                    return {'error': 'Patient not found'}, 404
                
                old_status = patient.status
                patient.status = new_status
                
                # If changing to Discharged, set discharge date and reset follow-up
                if new_status == 'Discharged' and old_status != 'Discharged':
                    if not patient.discharge_date:
                        patient.discharge_date = datetime.now()
                    patient.follow_up = 'Pending'
                
                db.commit()
                db.refresh(patient)
                
                message = f'Status updated from {old_status} to {new_status}'
                if new_status == 'Discharged' and old_status != 'Discharged':
                    message += '. SMS will be sent automatically.'
                
                return {
                    'success': True,
                    'message': message,
                    'patient_id': patient_id_str,
                    'patient_name': patient.name,
                    'old_status': old_status,
                    'new_status': new_status,
                    'follow_up': patient.follow_up
                }, 200
                
            finally:
                db.close()
                
        except Exception as e:
            return {'error': f'Error updating status: {str(e)}'}, 500


@discharge_ns.route('/batch-trigger')
class BatchDischargeTrigger(Resource):
    @discharge_ns.doc('batch_trigger_discharge')
    @discharge_ns.expect([discharge_trigger_model])
    @discharge_ns.response(200, 'Batch discharge triggered')
    @discharge_ns.response(400, 'Bad Request')
    @discharge_ns.response(500, 'Internal Server Error')
    def post(self):
        """
        Trigger discharge for multiple patients at once
        
        Accepts an array of patient discharge records
        """
        try:
            data = request.json
            
            if not isinstance(data, list):
                return {'error': 'Request body must be an array of patients'}, 400
            
            results = []
            errors = []
            
            for idx, patient_data in enumerate(data):
                try:
                    # Process each patient (reuse logic from single trigger)
                    name = patient_data.get('patient_name', '').strip()
                    phone = patient_data.get('phone_number', '').strip()
                    
                    if not name or not phone:
                        errors.append({
                            'index': idx,
                            'error': 'Missing patient_name or phone_number'
                        })
                        continue
                    
                    # Create/update patient (simplified - you can expand this)
                    db = SessionLocal()
                    try:
                        existing = db.query(Patient).filter_by(phone_number=phone).first()
                        
                        if existing:
                            existing.status = 'Discharged'
                            existing.follow_up = 'Pending'
                            existing.discharge_date = datetime.now()
                            db.commit()
                            patient_id = f'P{str(existing.id).zfill(6)}'
                        else:
                            new_patient = Patient(
                                name=name,
                                phone_number=phone,
                                hospital=patient_data.get('hospital'),
                                status='Discharged',
                                follow_up='Pending',
                                discharge_date=datetime.now()
                            )
                            db.add(new_patient)
                            db.commit()
                            db.refresh(new_patient)
                            patient_id = f'P{str(new_patient.id).zfill(6)}'
                        
                        results.append({
                            'patient_id': patient_id,
                            'name': name,
                            'phone': phone,
                            'status': 'success'
                        })
                    finally:
                        db.close()
                        
                except Exception as e:
                    errors.append({
                        'index': idx,
                        'name': patient_data.get('patient_name'),
                        'error': str(e)
                    })
            
            return {
                'success': True,
                'processed': len(results),
                'failed': len(errors),
                'results': results,
                'errors': errors if errors else None
            }, 200
            
        except Exception as e:
            return {'error': f'Error processing batch: {str(e)}'}, 500
