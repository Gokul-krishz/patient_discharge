import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
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
export class McpDemoComponent implements OnInit {
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

  constructor(
    private mcpService: McpService,
    private cdr: ChangeDetectorRef,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadArchitecture();
    this.loadStatus();
    this.loadTools();
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
}
