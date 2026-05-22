import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface FormResponses {
  recently_discharged: string;
  medication_changes: string;
  current_symptoms: string;
  care_team_notes: string;
  contact_request: string;
}

export interface LatestFormResponse {
  id: number;
  submitted_at: string | null;
  status: string;
  summary?: string;
  responses?: FormResponses;
}

export interface PatientApiItem {
  patient_id: string;
  name: string;
  phone_number: string;
  hospital: string;
  admission_date: string;
  discharge_date: string;
  status: string;
  follow_up: string;
  latest_form_response: LatestFormResponse | null;
}

export interface PatientFilters {
  search?: string;
  hospital?: string;
  status?: string;
  follow_up?: string;
}

export interface PendingFollowUpPatient {
  patient_id: string;
  name: string;
  initials: string;
  phone_number: string;
  hospital: string;
  discharge_date: string;
  discharge_date_iso: string | null;
  status: string;
  follow_up: string;
}

export interface PendingFollowUpResponse {
  count: number;
  patients: PendingFollowUpPatient[];
}

export interface SendFormLinkResponse {
  success: boolean;
  message: string;
  patient_id: string;
  patient_name: string;
  phone_number: string;
}

export interface HospitalsResponse {
  hospitals: string[];
  count: number;
}

export interface PatientListResponse {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  patients: PatientApiItem[];
}

export interface AdtPatientApiItem {
  patient_id: string;
  id: number;
  name: string;
  phone_number: string;
  hospital: string;
  admission_date: string | null;
  discharge_date: string | null;
  status: string;
  discharge_summary: any | null;
  created_at: string | null;
}

export interface AdtPatientListResponse {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  patients: AdtPatientApiItem[];
}

@Injectable({
  providedIn: 'root'
})
export class PatientService {
  private readonly BASE_URL = '/api';

  constructor(private http: HttpClient) {}

  getPatients(page: number = 1, perPage: number = 10, filters: PatientFilters = {}): Observable<PatientListResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());

    if (filters.search)    params = params.set('search',    filters.search);
    if (filters.hospital)  params = params.set('hospital',  filters.hospital);
    if (filters.status)    params = params.set('status',    filters.status);
    if (filters.follow_up) params = params.set('follow_up', filters.follow_up);

    return this.http.get<PatientListResponse>(`${this.BASE_URL}/patients/list`, { params });
  }

  getAdtPatients(page: number = 1, perPage: number = 10, filters: PatientFilters = {}): Observable<AdtPatientListResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('per_page', perPage.toString());

    if (filters.search)   params = params.set('search',   filters.search);
    if (filters.hospital) params = params.set('hospital', filters.hospital);
    if (filters.status)   params = params.set('status',   filters.status);

    return this.http.get<AdtPatientListResponse>(`${this.BASE_URL}/adt_patients`, { params });
  }

  getPendingFollowUps(): Observable<PendingFollowUpResponse> {
    return this.http.get<PendingFollowUpResponse>(`${this.BASE_URL}/patients/pending-followups`);
  }

  getHospitals(): Observable<HospitalsResponse> {
    return this.http.get<HospitalsResponse>(`${this.BASE_URL}/patients/hospitals`);
  }

  getAdtHospitals(): Observable<HospitalsResponse> {
    return this.http.get<HospitalsResponse>(`${this.BASE_URL}/adt_patients/hospitals`);
  }

  sendFormLink(patientId: string): Observable<SendFormLinkResponse> {
    return this.http.post<SendFormLinkResponse>(`${this.BASE_URL}/patients/send-form-link`, { patient_id: patientId });
  }
}
