import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PatientService, AdtPatientApiItem, PatientFilters, HospitalsResponse, SendFormLinkResponse } from '../services/patient.service';
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

  constructor(
    private router: Router,
    private patientService: PatientService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadPatients();
    this.loadHospitals();
  }

  loadHospitals(): void {
    this.patientService.getAdtHospitals().subscribe({
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
      phone:         p.phone_number,
      hospital:      p.hospital || '-',
      admissionDate: this.formatDate(p.admission_date),
      dischargeDate: this.formatDate(p.discharge_date),
      status:        p.status || 'Unknown',
      followUp:      '',
      avatar:        this.getInitials(p.name),
      latestFormResponse: null
    };
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

  onStatusButtonClick(patient: Patient): void {
    if (this.isDischargedBtn(patient) || this.isSending(patient.id)) return;

    this.sendingLink.add(patient.id);
    this.cdr.detectChanges();

    this.patientService.sendFormLink(patient.id).subscribe({
      next: (res: SendFormLinkResponse) => {
        this.sendingLink.delete(patient.id);
        this.dischargedPatients.add(patient.id);
        this.showToast(`Link sent to ${res.patient_name}`, 'success');
        this.cdr.detectChanges();
      },
      error: () => {
        this.sendingLink.delete(patient.id);
        this.showToast('Failed to send link. Please try again.', 'error');
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

  logout(): void {
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
}
