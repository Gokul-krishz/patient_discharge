import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ArchitectureLayer {
  id: string;
  name: string;
  type: string;
  description: string;
  tech: string;
  items?: ToolInfo[];
}

export interface ToolInfo {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  flow: string[];
}

export interface ArchitectureResponse {
  layers: ArchitectureLayer[];
  workflows: Workflow[];
}

export interface TraceStep {
  step: number;
  layer: string;
  layer_id: string;
  action: string;
  detail: string;
  status: string;
  data_sent: Record<string, any>;
}

export interface DemoTraceResponse {
  workflow: string;
  patient_name: string;
  total_steps: number;
  trace: TraceStep[];
  summary: string;
}

export interface MCPStatusResponse {
  agent: string;
  status: string;
  mcp_enabled: boolean;
  mcp_server: {
    status: string;
    registered_tools: number;
    tool_names: string[];
    total_executions: number;
  };
  context_size: number;
}

export interface MCPToolsResponse {
  agent: string;
  total_tools: number;
  tools: ToolInfo[];
}

export interface ExecutionHistoryResponse {
  executions: any[];
  total: number;
}

export interface ActionLog {
  id: number;
  patient_id: number;
  patient_name: string;
  phone_number: string;
  action: string;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface ActionLogsResponse {
  logs: ActionLog[];
  total: number;
}

@Injectable({
  providedIn: 'root'
})
export class McpService {
  private readonly BASE_URL = '/api';

  constructor(private http: HttpClient) {}

  getArchitecture(): Observable<ArchitectureResponse> {
    return this.http.get<ArchitectureResponse>(`${this.BASE_URL}/mcp/architecture`);
  }

  getStatus(): Observable<MCPStatusResponse> {
    return this.http.get<MCPStatusResponse>(`${this.BASE_URL}/mcp/status`);
  }

  getTools(): Observable<MCPToolsResponse> {
    return this.http.get<MCPToolsResponse>(`${this.BASE_URL}/mcp/tools`);
  }

  getExecutionHistory(limit: number = 20): Observable<ExecutionHistoryResponse> {
    return this.http.get<ExecutionHistoryResponse>(`${this.BASE_URL}/mcp/execution-history`, {
      params: { limit: limit.toString() }
    });
  }

  runDemoTrace(workflow: string, patientName: string = 'Demo Patient', phoneNumber: string = '+1234567890'): Observable<DemoTraceResponse> {
    return this.http.post<DemoTraceResponse>(`${this.BASE_URL}/mcp/demo-trace`, {
      workflow,
      patient_name: patientName,
      phone_number: phoneNumber
    });
  }

  getActionLogs(limit: number = 50, patientId?: number, action?: string): Observable<ActionLogsResponse> {
    let params: any = { limit: limit.toString() };
    if (patientId) params.patient_id = patientId.toString();
    if (action) params.action = action;
    
    return this.http.get<ActionLogsResponse>(`${this.BASE_URL}/action-logs`, { params });
  }

  getPatientActionLogs(patientId: number, limit: number = 50): Observable<ActionLogsResponse> {
    return this.http.get<ActionLogsResponse>(`${this.BASE_URL}/action-logs/${patientId}`, {
      params: { limit: limit.toString() }
    });
  }

  getPatients(): Observable<any> {
    return this.http.get<any>(`${this.BASE_URL}/patients/list`);
  }
}
