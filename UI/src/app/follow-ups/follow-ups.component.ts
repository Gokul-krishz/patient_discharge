import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { PatientService, PendingFollowUpPatient, SendFormLinkResponse } from '../services/patient.service';

type FollowUpPatient = PendingFollowUpPatient;

@Component({
  selector: 'app-follow-ups',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './follow-ups.component.html',
  styleUrl: './follow-ups.component.scss'
})
export class FollowUpsComponent implements OnInit {
  sidenavOpen = true;
  currentUser = 'Dr. Arjun Mehta';
  userRole = 'Nephrologist';
  searchQuery = '';
  isLoading = false;
  toastMessage = '';
  toastType: 'success' | 'error' = 'success';
  toastVisible = false;
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  followUpPatients: FollowUpPatient[] = [];

  constructor(private router: Router, private patientService: PatientService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.loadPendingFollowUps();
  }

  loadPendingFollowUps(): void {
    this.isLoading = true;
    this.patientService.getPendingFollowUps().subscribe({
      next: (response) => {
        this.followUpPatients = response.patients;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Failed to load pending follow-ups:', err);
        this.isLoading = false;
      }
    });
  }

  toggleSidenav(): void {
    this.sidenavOpen = !this.sidenavOpen;
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  logout(): void {
    this.router.navigate(['/login']);
  }

  getStatusClass(status: string): string {
    return status.toLowerCase().replace(' ', '-');
  }

  getPriorityClass(priority: string): string {
    return priority.toLowerCase();
  }

  sendLink(patient: FollowUpPatient): void {
    this.patientService.sendFormLink(patient.patient_id).subscribe({
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
}
