export interface LogEntry {
  timestamp: string
  message: string
  level: 'info' | 'success' | 'error' | 'warning'
  step?: number
}

export interface ProgressUpdate {
  step: number
  status: 'pending' | 'active' | 'completed' | 'error'
  progress: number
}

export interface FileDownload {
  name: string
  path: string
  size: string
  type: string
  download_url?: string
  artifact_id?: string
}

export interface SystemStatus {
  policy_exists: boolean
  questionnaire_exists: boolean
  api_key_configured: boolean
  skip_api: boolean
  automation_running: boolean
  policy_file: string
  questionnaire_file: string
}

export interface AutomationStep {
  id: number
  title: string
  icon: string
  status: 'pending' | 'active' | 'completed' | 'error'
}

export type LogLevel = 'info' | 'success' | 'error' | 'warning'
