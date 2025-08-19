// API Configuration
export const API_CONFIG = {
  // Use environment variable if available, fallback to localhost for development
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001',

  // API endpoints
  endpoints: {
    status: '/api/status',
    start: '/api/start',
    stop: '/api/stop',
    download: '/api/download',
  },
};

// Helper function to get full API URL
export function getApiUrl(endpoint: string = ''): string {
  return `${API_CONFIG.baseURL}${endpoint}`;
}
