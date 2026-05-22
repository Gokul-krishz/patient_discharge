import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PatientService, PatientApiItem, PatientFilters, PendingFollowUpPatient, HospitalsResponse, LatestFormResponse, SendFormLinkResponse } from '../services/patient.service';

interface StatCard {
  title: string;
  value: number;
  change: string;
  icon: string;
  color: string;
}

export interface Patient {
  id: string;
  name: string;
  phone: string;
  hospital: string;
  admissionDate: string;
  dischargeDate: string;
  status: string;
  followUp: string;
  avatar: string;
  latestFormResponse: LatestFormResponse | null;
}

interface PendingFollowUp {
  id: string;
  name: string;
  patientId: string;
  date: string;
  avatar: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  sidenavOpen = true;
  currentUser = 'Dr. Arjun Mehta';
  userRole = 'Nephrologist';
  isLoading = false;
  errorMessage = '';

  totalPatients = 0;
  totalPages = 0;
  currentPage = 1;

  stats: StatCard[] = [
    { title: 'Total Patients',       value: 0,  change: '12% from last month', icon: 'users',    color: '#4A90E2' },
    { title: 'Active Kidney Care',   value: 0,  change: '8% from last month',  icon: 'kidney',   color: '#27AE60' },
    { title: 'Recently Discharged',  value: 0,  change: '15% from last month', icon: 'discharge',color: '#F39C12' },
    { title: 'Pending Follow Ups',   value: 0,  change: '5% from last month',  icon: 'followup', color: '#9B59B6' }
  ];

  patients: Patient[] = [];
  pendingFollowUps: PendingFollowUp[] = [];

  searchQuery = '';
  selectedHospital = '';
  selectedStatus = '';
  selectedFollowUp = '';
  hospitals: string[] = [];
  private searchTimer: ReturnType<typeof setTimeout> | null = null;

  showModal = false;
  showSummary = true;
  showQA = true;
  selectedPatient: Patient | null = null;

  toastMessage = '';
  toastType: 'success' | 'error' = 'success';
  toastVisible = false;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  readonly responseLabels: Record<string, string> = {
    recently_discharged: 'Were you recently discharged?',
    medication_changes: 'Were there any medication changes?',
    current_symptoms: 'What are your current symptoms?',
    care_team_notes: 'Did you review care team notes?',
    contact_request: 'Do you want the care team to contact you?'
  };

  constructor(private router: Router, private patientService: PatientService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.loadPatients();
    this.loadPendingFollowUps();
    this.loadHospitals();
  }

  loadHospitals(): void {
    this.patientService.getHospitals().subscribe({
      next: (response: HospitalsResponse) => {
        this.hospitals = response.hospitals;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load hospitals:', err);
      }
    });
  }

  loadPendingFollowUps(): void {
    this.patientService.getPendingFollowUps().subscribe({
      next: (response) => {
        this.stats[3].value = response.count;
        this.pendingFollowUps = response.patients.slice(0, 4).map((p: PendingFollowUpPatient) => ({
          id: p.patient_id,
          name: p.name,
          patientId: p.patient_id,
          date: p.discharge_date !== 'Unknown' ? p.discharge_date : 'N/A',
          avatar: p.initials
        }));
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load pending follow-ups:', err);
      }
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
    if (this.searchQuery.trim())   filters.search    = this.searchQuery.trim();
    if (this.selectedHospital)     filters.hospital  = this.selectedHospital;
    if (this.selectedStatus)       filters.status    = this.selectedStatus;
    if (this.selectedFollowUp)     filters.follow_up = this.selectedFollowUp;

    this.patientService.getPatients(page, 10, filters).subscribe({
      next: (response) => {
        this.totalPatients = response.total;
        this.totalPages = response.total_pages;
        this.currentPage = response.page;

        this.patients = response.patients.map(p => this.mapToPatient(p));

        const discharged = response.patients.filter(p => p.status === 'Discharged').length;

        this.stats[0].value = response.total;
        this.stats[2].value = discharged;

        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load patients:', err);
        this.errorMessage = 'Failed to load patient data. Please try again.';
        this.isLoading = false;
      }
    });
  }

  private mapToPatient(p: PatientApiItem): Patient {
    return {
      id: p.patient_id,
      name: p.name,
      phone: p.phone_number,
      hospital: p.hospital,
      admissionDate: p.admission_date,
      dischargeDate: p.discharge_date,
      status: p.status,
      followUp: p.follow_up,
      avatar: this.getInitials(p.name),
      latestFormResponse: p.latest_form_response
    };
  }

  private getInitials(name: string): string {
    return name
      .split(' ')
      .map(w => w[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  }

  toggleSidenav(): void {
    this.sidenavOpen = !this.sidenavOpen;
  }

  logout(): void {
    this.router.navigate(['/login']);
  }

  openPatientModal(patient: Patient): void {
    this.selectedPatient = patient;
    this.showModal = true;
    this.showSummary = true;
    this.showQA = true;
  }

  sendLink(patientId: string): void {
    this.patientService.sendFormLink(patientId).subscribe({
      next: (res: SendFormLinkResponse) => {
        this.showToast(`Link sent to ${res.patient_name}`, 'success');
        this.loadPendingFollowUps();
      },
      error: () => {
        this.showToast('Failed to send link. Please try again.', 'error');
      }
    });
  }

  private showToast(message: string, type: 'success' | 'error'): void {
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toastMessage = message;
    this.toastType = type;
    this.toastVisible = true;
    this.cdr.detectChanges();
    this.toastTimer = setTimeout(() => {
      this.toastVisible = false;
      this.cdr.detectChanges();
    }, 3000);
  }

  closeModal(): void {
    this.showModal = false;
    this.selectedPatient = null;
  }

  navigateToFollowUps(): void {
    this.router.navigate(['/follow-ups']);
  }

  navigateToEditTrigger(): void {
    this.router.navigate(['/edit-trigger']);
  }

  getStatusClass(status: string): string {
    return status.toLowerCase().replace(/\s+/g, '-');
  }

  getFollowUpClass(followUp: string): string {
    return followUp.toLowerCase().replace(/\s+/g, '-');
  }

  goToPage(page: number): void {
    if (page >= 1 && page <= this.totalPages) {
      this.loadPatients(page);
    }
  }

  getPageNumbers(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i + 1);
  }
}
