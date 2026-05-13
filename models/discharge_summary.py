"""
Data models for discharge summary
"""
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class DischargeSummary:
    """Discharge summary data model"""
    patient_name: str
    hospitalization_reason: str
    medication_changes: List[str]
    current_symptoms: List[str]
    outcomes_after_discharge: List[str]
    care_team_updates: List[str]
    diet_restrictions: List[str]
    risk_indicators: List[str]
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'patient_name': self.patient_name,
            'hospitalization_reason': self.hospitalization_reason,
            'medication_changes': self.medication_changes,
            'current_symptoms': self.current_symptoms,
            'outcomes_after_discharge': self.outcomes_after_discharge,
            'care_team_updates': self.care_team_updates,
            'diet_restrictions': self.diet_restrictions,
            'risk_indicators': self.risk_indicators
        }
