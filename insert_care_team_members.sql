-- SQL Script to insert 5 care team members
-- First, ensure we have a patient (insert one if needed)

-- Insert a sample patient if one doesn't exist
INSERT INTO patients (name, phone_number, created_at)
VALUES ('John Doe', '+919677863998', NOW())
ON CONFLICT (phone_number) DO NOTHING;

-- Get the patient ID (adjust this based on your actual patient)
-- For this script, we'll assume patient_id = 1
-- You can change this to match your actual patient ID

-- Insert 5 care team members
INSERT INTO care_team_members (
    patient_id, 
    name, 
    role, 
    phone_number, 
    email, 
    specialty, 
    is_primary, 
    notes, 
    created_at, 
    updated_at
) VALUES 
    -- Primary Nephrologist
    (
        1,
        'Dr. Sarah Johnson',
        'Nephrologist',
        '+1-555-0101',
        'sarah.johnson@hospital.com',
        'Nephrology',
        TRUE,
        'Primary nephrologist, specializes in chronic kidney disease and dialysis management',
        NOW(),
        NOW()
    ),
    
    -- Dialysis Nurse
    (
        1,
        'Maria Garcia',
        'Dialysis Nurse',
        '+1-555-0102',
        'maria.garcia@hospital.com',
        'Dialysis Care',
        FALSE,
        'Manages dialysis sessions, monitors vital signs during treatment',
        NOW(),
        NOW()
    ),
    
    -- Renal Dietitian
    (
        1,
        'David Chen',
        'Dietitian',
        '+1-555-0103',
        'david.chen@hospital.com',
        'Renal Nutrition',
        FALSE,
        'Provides dietary counseling for kidney disease patients, manages fluid and electrolyte balance',
        NOW(),
        NOW()
    ),
    
    -- Social Worker
    (
        1,
        'Emily Rodriguez',
        'Social Worker',
        '+1-555-0104',
        'emily.rodriguez@hospital.com',
        'Medical Social Work',
        FALSE,
        'Assists with insurance, transportation, and psychosocial support',
        NOW(),
        NOW()
    ),
    
    -- Pharmacist
    (
        1,
        'Dr. Michael Thompson',
        'Pharmacist',
        '+1-555-0105',
        'michael.thompson@hospital.com',
        'Clinical Pharmacy',
        FALSE,
        'Reviews medications, manages drug interactions, provides medication counseling',
        NOW(),
        NOW()
    );

-- Verify the insertions
SELECT 
    ctm.id,
    ctm.name,
    ctm.role,
    ctm.specialty,
    ctm.is_primary,
    p.name as patient_name
FROM care_team_members ctm
JOIN patients p ON ctm.patient_id = p.id
ORDER BY ctm.is_primary DESC, ctm.id;
