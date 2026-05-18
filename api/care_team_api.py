"""
Care Team API endpoints
"""
from flask_restx import Namespace, Resource, fields
from services.care_team_service import CareTeamService

care_team_ns = Namespace('care-team', description='Care team member management operations')

# Initialize service
care_team_service = CareTeamService()

# Request/Response models
care_team_member_model = care_team_ns.model('CareTeamMember', {
    'patient_id': fields.Integer(required=True, description='Patient ID'),
    'name': fields.String(required=True, description='Care team member name'),
    'role': fields.String(required=True, description='Role (e.g., Nephrologist, Nurse, Dietitian)'),
    'phone_number': fields.String(description='Contact phone number'),
    'email': fields.String(description='Contact email'),
    'specialty': fields.String(description='Medical specialty'),
    'is_primary': fields.Boolean(description='Is this the primary care team member?', default=False),
    'notes': fields.String(description='Additional notes')
})

update_care_team_member_model = care_team_ns.model('UpdateCareTeamMember', {
    'name': fields.String(description='Care team member name'),
    'role': fields.String(description='Role'),
    'phone_number': fields.String(description='Contact phone number'),
    'email': fields.String(description='Contact email'),
    'specialty': fields.String(description='Medical specialty'),
    'is_primary': fields.Boolean(description='Is this the primary care team member?'),
    'notes': fields.String(description='Additional notes')
})


@care_team_ns.route('/members')
class CareTeamMemberList(Resource):
    @care_team_ns.doc('add_care_team_member')
    @care_team_ns.expect(care_team_member_model)
    def post(self):
        """Add a new care team member to a patient"""
        try:
            data = care_team_ns.payload
            result = care_team_service.add_care_team_member(
                patient_id=data['patient_id'],
                name=data['name'],
                role=data['role'],
                phone_number=data.get('phone_number'),
                email=data.get('email'),
                specialty=data.get('specialty'),
                is_primary=data.get('is_primary', False),
                notes=data.get('notes')
            )
            return result, 201
        except ValueError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': f'Error adding care team member: {str(e)}'}, 500


@care_team_ns.route('/members/<int:member_id>')
class CareTeamMemberDetail(Resource):
    @care_team_ns.doc('update_care_team_member')
    @care_team_ns.expect(update_care_team_member_model)
    def put(self, member_id):
        """Update a care team member's information"""
        try:
            data = care_team_ns.payload
            result = care_team_service.update_care_team_member(member_id, **data)
            return result, 200
        except ValueError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': f'Error updating care team member: {str(e)}'}, 500
    
    @care_team_ns.doc('delete_care_team_member')
    def delete(self, member_id):
        """Delete a care team member"""
        try:
            result = care_team_service.delete_care_team_member(member_id)
            return result, 200
        except ValueError as e:
            return {'error': str(e)}, 404
        except Exception as e:
            return {'error': f'Error deleting care team member: {str(e)}'}, 500


@care_team_ns.route('/patient/<int:patient_id>')
class PatientCareTeam(Resource):
    @care_team_ns.doc('get_patient_care_team')
    def get(self, patient_id):
        """Get all care team members for a patient"""
        try:
            members = care_team_service.get_care_team_by_patient(patient_id)
            return {
                'patient_id': patient_id,
                'care_team_members': members,
                'count': len(members)
            }, 200
        except Exception as e:
            return {'error': f'Error retrieving care team: {str(e)}'}, 500


@care_team_ns.route('/patient/<int:patient_id>/primary')
class PrimaryCareTeamMember(Resource):
    @care_team_ns.doc('get_primary_care_member')
    def get(self, patient_id):
        """Get the primary care team member for a patient"""
        try:
            member = care_team_service.get_primary_care_member(patient_id)
            if member:
                return member, 200
            else:
                return {'message': 'No primary care team member found for this patient'}, 404
        except Exception as e:
            return {'error': f'Error retrieving primary care member: {str(e)}'}, 500
