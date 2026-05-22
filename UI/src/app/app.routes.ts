import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: 'login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () => import('./login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'follow-ups',
    loadComponent: () => import('./follow-ups/follow-ups.component').then(m => m.FollowUpsComponent)
  },
  {
    path: 'edit-trigger',
    loadComponent: () => import('./edit-trigger/adtPatient').then(m => m.AdtPatientComponent)
  }
];
