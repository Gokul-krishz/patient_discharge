import { Component, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import {
  McpService,
  ArchitectureLayer,
  Workflow,
  TraceStep,
  ToolInfo,
  MCPStatusResponse
} from '../services/mcp.service';

@Component({
  selector: 'app-mcp-demo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './mcp-demo.component.html',
  styleUrl: './mcp-demo.component.scss'
})
export class McpDemoComponent implements OnInit, OnDestroy {
  sidenavOpen = true;

  layers: ArchitectureLayer[] = [];
  workflows: Workflow[] = [];
  tools: ToolInfo[] = [];
  serverStatus: MCPStatusResponse | null = null;

  selectedWorkflow = 'form_outreach';
  demoPatientName = 'John Smith';
  demoPhone = '+919876543210';

  traceSteps: TraceStep[] = [];
  activeStepIndex = -1;
  isTracing = false;
  traceSummary = '';

  activeLayerId = '';
  expandedTool: string | null = null;

  isLoading = true;

  // Action logs
  actionLogs: any[] = [];
  loadingLogs = false;
  private logsRefreshInterval: any;

  // Patient search and filter
  patients: any[] = [];
  loadingPatients = false;
  selectedPatientId: string | undefined = undefined;
  filteredLogs: any[] = [];
  loadingFilteredLogs = false;
  fromDate: string | undefined = undefined;
  toDate: string | undefined = undefined;
  
  // Filter modal
  showFilterModal = false;
  showActionsDropdown = false;
  availableActions: string[] = [
    'SMS Sent',
    'Form Link Sent',
    'Form Submitted',
    'Conversation Started',
    'Conversation Completed',
    'AI Summary Generated',
    'Patient Created',
    'Patient Updated',
    'Care Team Assigned',
    'Follow-up Scheduled',
    'Notification Sent'
  ];
  selectedActions: string[] = [];

  constructor(
    private mcpService: McpService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadArchitecture();
    this.loadStatus();
    this.loadTools();
    this.loadActionLogs();
    this.loadPatients();
    // Don't load patient logs on initial load - wait for user to select a patient
    
    // Auto-refresh logs every 10 seconds
    this.logsRefreshInterval = setInterval(() => {
      this.loadActionLogs();
    }, 10000);
  }

  ngOnDestroy(): void {
    if (this.logsRefreshInterval) {
      clearInterval(this.logsRefreshInterval);
    }
  }

  loadArchitecture(): void {
    this.mcpService.getArchitecture().subscribe({
      next: (res) => {
        this.layers = res.layers;
        this.workflows = res.workflows;
        this.isLoading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.isLoading = false;
      }
    });
  }

  loadStatus(): void {
    this.mcpService.getStatus().subscribe({
      next: (res) => {
        this.serverStatus = res;
        this.cdr.detectChanges();
      }
    });
  }

  loadTools(): void {
    this.mcpService.getTools().subscribe({
      next: (res) => {
        this.tools = res.tools;
        this.cdr.detectChanges();
      }
    });
  }

  runTrace(): void {
    if (this.isTracing) return;

    this.isTracing = true;
    this.traceSteps = [];
    this.activeStepIndex = -1;
    this.traceSummary = '';
    this.activeLayerId = '';
    this.cdr.detectChanges();

    this.mcpService.runDemoTrace(this.selectedWorkflow, this.demoPatientName, this.demoPhone).subscribe({
      next: (res) => {
        this.animateTrace(res.trace, res.summary);
      },
      error: () => {
        this.isTracing = false;
        this.cdr.detectChanges();
      }
    });
  }

  private animateTrace(steps: TraceStep[], summary: string): void {
    let index = 0;
    const interval = setInterval(() => {
      if (index < steps.length) {
        this.traceSteps.push(steps[index]);
        this.activeStepIndex = index;
        this.activeLayerId = steps[index].layer_id;
        this.cdr.detectChanges();

        // Scroll the log to bottom
        setTimeout(() => {
          const logEl = document.querySelector('.trace-log');
          if (logEl) logEl.scrollTop = logEl.scrollHeight;
        }, 50);

        index++;
      } else {
        clearInterval(interval);
        this.traceSummary = summary;
        this.isTracing = false;
        this.activeLayerId = '';
        this.cdr.detectChanges();
      }
    }, 800);
  }

  toggleTool(toolName: string): void {
    this.expandedTool = this.expandedTool === toolName ? null : toolName;
  }

  getParamKeys(params: Record<string, any>): string[] {
    return Object.keys(params);
  }

  getWorkflowName(): string {
    const wf = this.workflows.find(w => w.id === this.selectedWorkflow);
    return wf ? wf.name : this.selectedWorkflow;
  }

  isLayerCompleted(layerId: string): boolean {
    return this.traceSteps.some(s => s.layer_id === layerId && s.status !== 'pending');
  }

  isArrowActive(index: number): boolean {
    if (this.activeStepIndex < 0) return false;
    const currentLayerId = this.traceSteps[this.activeStepIndex]?.layer_id;
    if (!currentLayerId) return false;
    const layerIndex = this.layers.findIndex(l => l.id === currentLayerId);
    return index === layerIndex - 1 || index === layerIndex;
  }

  getLayerIcon(type: string): string {
    const icons: Record<string, string> = {
      frontend: 'M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z',
      api: 'M13 10V3L4 14h7v7l9-11h-7z',
      agent: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
      mcp: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
      tools: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
      services: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z'
    };
    return icons[type] || '';
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }

  navigateToEditTrigger(): void {
    this.router.navigate(['/edit-trigger']);
  }

  logout(): void {
    this.router.navigate(['/login']);
  }

  // Action Logs Methods
  loadActionLogs(): void {
    this.loadingLogs = true;
    this.mcpService.getActionLogs(30).subscribe({
      next: (res: any) => {
        let logs = res.logs || [];
        // Sort by date and time (newest first)
        this.actionLogs = this.sortLogsByDate(logs);
        this.loadingLogs = false;
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        console.error('Error loading action logs:', err);
        this.loadingLogs = false;
        this.actionLogs = [];
        this.cdr.detectChanges();
      }
    });
  }

  formatLogTime(timestamp: string): string {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    
    return date.toLocaleString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  }

  getActionType(action: string): string {
    const actionMap: Record<string, string> = {
      'SMS Sent': 'sms',
      'Form Link Sent': 'form',
      'Form Submitted': 'form',
      'Conversation Started': 'conversation',
      'Conversation Completed': 'conversation',
      'AI Summary Generated': 'ai',
      'Patient Created': 'patient',
      'Patient Updated': 'patient',
      'Care Team Assigned': 'team',
      'Follow-up Scheduled': 'schedule',
      'Notification Sent': 'notification'
    };
    return actionMap[action] || 'default';
  }

  hasMetadata(metadata: any): boolean {
    return metadata && typeof metadata === 'object' && Object.keys(metadata).length > 0;
  }

  formatJSON(obj: any): string {
    try {
      return JSON.stringify(obj, null, 2);
    } catch (e) {
      return String(obj);
    }
  }

  // Patient search and filter methods
  loadPatients(): void {
    this.loadingPatients = true;
    this.mcpService.getPatients().subscribe({
      next: (res: any) => {
        this.patients = res.patients || [];
        this.loadingPatients = false;
        this.cdr.detectChanges();
      },
      error: (err) => {
        console.error('Error loading patients:', err);
        this.loadingPatients = false;
        this.patients = [];
        this.cdr.detectChanges();
      }
    });
  }

  searchPatientLogs(): void {
    console.log('searchPatientLogs called with selectedPatientId:', this.selectedPatientId);
    console.log('Date range:', this.fromDate, 'to', this.toDate);
    console.log('Selected actions:', this.selectedActions);
    
    // Check if at least one filter is provided
    const hasPatientFilter = this.selectedPatientId && this.selectedPatientId !== '';
    const hasDateFilter = this.fromDate || this.toDate;
    const hasActionFilter = this.selectedActions.length > 0;
    
    if (!hasPatientFilter && !hasDateFilter && !hasActionFilter) {
      console.log('No filters selected, clearing results');
      this.filteredLogs = [];
      this.loadingFilteredLogs = false;
      this.cdr.detectChanges();
      return;
    }
    
    this.loadingFilteredLogs = true;
    
    let patientId: number | undefined = undefined;
    
    if (hasPatientFilter) {
      patientId = parseInt(this.selectedPatientId!.toString());
      
      if (isNaN(patientId)) {
        console.error('Invalid patient ID:', this.selectedPatientId);
        this.filteredLogs = [];
        this.loadingFilteredLogs = false;
        this.cdr.detectChanges();
        return;
      }
    }
    
    console.log('Fetching logs with filters - Patient ID:', patientId, 'Date range:', hasDateFilter, 'Actions:', hasActionFilter);
    
    // Use query parameter API: /api/action-logs?limit=100&patient_id={id} (if patient selected)
    // If no patient selected, fetch all logs and filter by date/action
    this.mcpService.getActionLogs(100, patientId).subscribe({
      next: (res: any) => {
        console.log('Received logs response:', res);
        let logs = res.logs || [];
        
        // Apply date filtering on the client side
        if (hasDateFilter) {
          logs = this.filterLogsByDateRange(logs);
          console.log('After date filtering:', logs.length, 'logs');
        }
        
        // Apply action filtering on the client side
        if (hasActionFilter) {
          logs = this.filterLogsByActions(logs);
          console.log('After action filtering:', logs.length, 'logs');
        }
        
        // Sort by date and time (newest first)
        logs = this.sortLogsByDate(logs);
        console.log('Sorted logs by date (newest first)');
        
        this.filteredLogs = logs;
        console.log('Filtered logs count:', this.filteredLogs.length);
        this.loadingFilteredLogs = false;
        this.cdr.detectChanges();
      },
      error: (err: any) => {
        console.error('Error loading logs:', err);
        this.filteredLogs = [];
        this.loadingFilteredLogs = false;
        this.cdr.detectChanges();
      }
    });
  }

  filterLogsByDateRange(logs: any[]): any[] {
    return logs.filter(log => {
      if (!log.timestamp) return false;
      
      const logDate = new Date(log.timestamp);
      logDate.setHours(0, 0, 0, 0); // Reset time to start of day for comparison
      
      if (this.fromDate) {
        const fromDateTime = new Date(this.fromDate);
        fromDateTime.setHours(0, 0, 0, 0);
        if (logDate < fromDateTime) return false;
      }
      
      if (this.toDate) {
        const toDateTime = new Date(this.toDate);
        toDateTime.setHours(23, 59, 59, 999); // End of day
        if (logDate > toDateTime) return false;
      }
      
      return true;
    });
  }

  filterLogsByActions(logs: any[]): any[] {
    return logs.filter(log => this.selectedActions.includes(log.action));
  }

  sortLogsByDate(logs: any[]): any[] {
    return logs.sort((a, b) => {
      const dateA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const dateB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return dateB - dateA; // Descending order (newest first)
    });
  }

  // Modal methods
  openFilterModal(): void {
    this.showFilterModal = true;
  }

  closeFilterModal(): void {
    this.showFilterModal = false;
  }

  applyFilters(): void {
    this.closeFilterModal();
    this.searchPatientLogs();
  }

  clearModalFilters(): void {
    this.fromDate = undefined;
    this.toDate = undefined;
    this.selectedActions = [];
  }

  clearFilters(): void {
    this.fromDate = undefined;
    this.toDate = undefined;
    this.selectedPatientId = undefined;
    this.selectedActions = [];
    this.filteredLogs = [];
    this.cdr.detectChanges();
  }

  toggleAction(action: string): void {
    const index = this.selectedActions.indexOf(action);
    if (index > -1) {
      this.selectedActions.splice(index, 1);
    } else {
      this.selectedActions.push(action);
    }
  }

  isActionSelected(action: string): boolean {
    return this.selectedActions.includes(action);
  }

  getActiveFiltersCount(): number {
    let count = 0;
    if (this.fromDate) count++;
    if (this.toDate) count++;
    if (this.selectedActions.length > 0) count++;
    return count;
  }

  toggleActionsDropdown(): void {
    this.showActionsDropdown = !this.showActionsDropdown;
  }

  exportToCSV(): void {
    if (this.filteredLogs.length === 0) {
      return;
    }

    // Define CSV headers
    const headers = ['Patient Name', 'Phone Number', 'Action', 'Timestamp', 'Metadata'];
    
    // Convert logs to CSV rows
    const csvRows = this.filteredLogs.map(log => {
      const metadata = log.metadata && typeof log.metadata === 'object' 
        ? JSON.stringify(log.metadata).replace(/"/g, '""') // Escape quotes
        : '';
      
      // Add tab prefix to phone number to force text format in Excel
      const phoneNumber = log.phone_number ? `\t${log.phone_number}` : '';
      
      return [
        log.patient_name || 'Unknown',
        phoneNumber,
        log.action || '',
        log.timestamp || '',
        metadata
      ].map(field => `"${field}"`).join(',');
    });

    // Combine headers and rows
    const csvContent = [
      headers.join(','),
      ...csvRows
    ].join('\n');

    // Create blob and download
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    // Generate filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `patient_logs_${timestamp}.csv`;
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log(`Exported ${this.filteredLogs.length} logs to ${filename}`);
  }
}
