import { Component, OnInit, ChangeDetectorRef, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PatientService, AdtPatientApiItem, PatientFilters, HospitalsResponse, SendFormLinkResponse, CareTeamMember, AddAdtPatientPayload } from '../services/patient.service';
import { Patient } from '../dashboard/dashboard.component';

@Component({
  selector: 'app-adt-patient',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './adtPatient.html',
  styleUrl: './adtPatient.scss'
})
export class AdtPatientComponent implements OnInit {
  sidenavOpen = true;
  isLoading = false;
  errorMessage = '';

  totalPatients = 0;
  totalPages = 0;
  currentPage = 1;

  patients: Patient[] = [];
  hospitals: string[] = [];
  careTeamMembers: CareTeamMember[] = [];

  dischargedPatients = new Set<string>();
  sendingLink = new Set<string>();

  searchQuery = '';
  selectedHospital = '';
  selectedStatus = '';
  private searchTimer: ReturnType<typeof setTimeout> | null = null;

  toastMessage = '';
  toastType: 'success' | 'error' = 'success';
  toastVisible = false;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  showAddPatientModal = false;
  isSubmitting = false;
  newPatient = {
    patient_name: '',
    mobile_number: '',
    hospital: '',
    description: '',
    care_team: 0
  };

  showConfirmDischarge = false;
  selectedPatientForDischarge: Patient | null = null;
  openDropdownId: string | null = null;
  showProfileDropdown = false;

  constructor(
    private router: Router,
    private patientService: PatientService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadPatients();
    this.loadHospitals();
    this.loadCareTeamMembers();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: Event): void {
    this.openDropdownId = null;
    this.showProfileDropdown = false;
  }

  loadHospitals(): void {
    this.patientService.getHospitals().subscribe({
      next: (response: HospitalsResponse) => {
        this.hospitals = response.hospitals;
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Failed to load ADT hospitals:', err)
    });
  }

  applyFilters(): void {
    this.loadPatients(1);
  }

  onSearchChange(): void {
    if (this.searchTimer) clearTimeout(this.searchTimer);
    this.searchTimer = setTimeout(() => this.loadPatients(1), 400);
  }

  loadPatients(page: number = 1): void {
    this.isLoading = true;
    this.errorMessage = '';

    const filters: PatientFilters = {};
    if (this.searchQuery.trim()) filters.search   = this.searchQuery.trim();
    if (this.selectedHospital)   filters.hospital = this.selectedHospital;
    if (this.selectedStatus)     filters.status   = this.selectedStatus;

    this.patientService.getAdtPatients(page, 10, filters).subscribe({
      next: (response) => {
        this.totalPatients  = response.total;
        this.totalPages     = response.total_pages;
        this.currentPage    = response.page;
        this.patients       = response.patients.map(p => this.mapToPatient(p));
        this.isLoading      = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load ADT patients:', err);
        this.errorMessage = 'Failed to load patient data. Please try again.';
        this.isLoading = false;
      }
    });
  }

  private mapToPatient(p: AdtPatientApiItem): Patient {
    return {
      id:            p.patient_id,
      name:          p.name,
      phone:         this.formatPhoneNumber(p.phone_number),
      hospital:      p.hospital || '-',
      admissionDate: this.formatDate(p.admission_date),
      dischargeDate: this.formatDate(p.discharge_date),
      status:        p.status || 'Unknown',
      followUp:      '',
      avatar:        this.getInitials(p.name),
      latestFormResponse: null
    };
  }

  private formatPhoneNumber(phone: string): string {
    // Replace +91 with +1 for display purposes only
    if (phone && phone.startsWith('+91')) {
      return phone.replace('+91', '+1');
    }
    return phone;
  }

  private formatDate(iso: string | null): string {
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  }

  private getInitials(name: string): string {
    return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
  }

  isDischargedBtn(patient: Patient): boolean {
    return patient.status === 'Discharged' || this.dischargedPatients.has(patient.id);
  }

  isSending(patientId: string): boolean {
    return this.sendingLink.has(patientId);
  }

  toggleDropdown(patientId: string, event: Event): void {
    event.stopPropagation();
    this.openDropdownId = this.openDropdownId === patientId ? null : patientId;
  }

  onStatusChange(patient: Patient, newStatus: string): void {
    this.openDropdownId = null;
    
    if (newStatus === 'Discharged' && patient.status !== 'Discharged') {
      this.selectedPatientForDischarge = patient;
      this.showConfirmDischarge = true;
    }
  }

  closeConfirmDischarge(): void {
    this.showConfirmDischarge = false;
    this.selectedPatientForDischarge = null;
  }

  confirmDischarge(): void {
    if (!this.selectedPatientForDischarge) return;

    const patient = this.selectedPatientForDischarge;
    this.sendingLink.add(patient.id);
    this.showConfirmDischarge = false;
    this.cdr.detectChanges();

    this.patientService.sendFormLink(patient.id).subscribe({
      next: (res: SendFormLinkResponse) => {
        this.sendingLink.delete(patient.id);
        this.dischargedPatients.add(patient.id);
        this.showToast(`Link sent to ${res.patient_name}. Patient discharged successfully.`, 'success');
        this.selectedPatientForDischarge = null;
        this.loadPatients(this.currentPage);
        this.cdr.detectChanges();
      },
      error: () => {
        this.sendingLink.delete(patient.id);
        this.showToast('Failed to send link. Please try again.', 'error');
        this.selectedPatientForDischarge = null;
        this.cdr.detectChanges();
      }
    });
  }

  private showToast(message: string, type: 'success' | 'error'): void {
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toastMessage = message;
    this.toastType    = type;
    this.toastVisible = true;
    this.cdr.detectChanges();
    this.toastTimer = setTimeout(() => {
      this.toastVisible = false;
      this.cdr.detectChanges();
    }, 3000);
  }

  toggleProfileDropdown(event: Event): void {
    event.stopPropagation();
    this.showProfileDropdown = !this.showProfileDropdown;
  }

  logout(): void {
    this.showProfileDropdown = false;
    this.router.navigate(['/login']);
  }

  navigateToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.loadPatients(page);
    }
  }

  getPageNumbers(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }

  loadCareTeamMembers(): void {
    console.log('Loading care team members...');
    this.patientService.getCareTeamMembers().subscribe({
      next: (response) => {
        console.log('Care team members response:', response);
        this.careTeamMembers = response.care_team_members;
        console.log('Care team members loaded:', this.careTeamMembers);
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load care team members:', err);
        this.showToast('Failed to load care team members', 'error');
      }
    });
  }

  openAddPatientModal(): void {
    this.showAddPatientModal = true;
    this.newPatient = {
      patient_name: '',
      mobile_number: '',
      hospital: '',
      description: '',
      care_team: 0
    };
  }

  closeAddPatientModal(): void {
    this.showAddPatientModal = false;
  }

  isFormValid(): boolean {
    return !!(
      this.newPatient.patient_name?.trim() &&
      this.newPatient.mobile_number?.trim() &&
      this.newPatient.hospital?.trim() &&
      this.newPatient.care_team > 0
    );
  }

  onAddPatient(): void {
    if (!this.newPatient.patient_name || !this.newPatient.mobile_number || !this.newPatient.hospital || !this.newPatient.care_team) {
      this.showToast('Please fill in all required fields', 'error');
      return;
    }

    this.isSubmitting = true;
    
    // Add +91 prefix to mobile number if not already present
    let mobileNumber = this.newPatient.mobile_number.trim();
    if (!mobileNumber.startsWith('+91')) {
      mobileNumber = '+91' + mobileNumber;
    }
    
    const payload: AddAdtPatientPayload = {
      patient_name: this.newPatient.patient_name,
      mobile_number: mobileNumber,
      hospital: this.newPatient.hospital,
      description: this.newPatient.description,
      care_team: this.newPatient.care_team || undefined
    };

    this.patientService.addAdtPatient(payload).subscribe({
      next: (response) => {
        this.isSubmitting = false;
        this.cdr.detectChanges();
        this.closeAddPatientModal();
        this.showToast('Patient added successfully', 'success');
        this.loadPatients(1);
      },
      error: (err) => {
        this.isSubmitting = false;
        this.showToast('Failed to add patient. Please try again.', 'error');
        console.error('Error adding patient:', err);
        this.cdr.detectChanges();
      }
    });
  }
}
