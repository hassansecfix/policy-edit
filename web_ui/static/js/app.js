// Policy Automation Dashboard - Frontend JavaScript
class PolicyAutomationDashboard {
    constructor() {
        this.socket = null;
        this.automationRunning = false;
        this.logCount = 0;
        this.init();
    }

    init() {
        this.initializeSocket();
        this.bindEvents();
        this.checkStatus();
        this.setupAutoScroll();
    }

    initializeSocket() {
        // Initialize Socket.IO connection
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });

        this.socket.on('log_message', (data) => {
            this.addLogEntry(data);
        });

        this.socket.on('progress_update', (data) => {
            this.updateProgress(data);
        });

        this.socket.on('files_ready', (data) => {
            this.showDownloadLinks(data.files);
        });

        this.socket.on('logs_cleared', () => {
            this.clearLogs();
        });
    }

    bindEvents() {
        // Start automation button
        document.getElementById('start-automation').addEventListener('click', () => {
            this.startAutomation();
        });

        // Stop automation button
        document.getElementById('stop-automation').addEventListener('click', () => {
            this.stopAutomation();
        });

        // Clear logs button
        document.getElementById('clear-logs').addEventListener('click', () => {
            this.socket.emit('clear_logs');
        });

        // Skip API checkbox
        document.getElementById('skipApiCheck').addEventListener('change', (e) => {
            this.updateSkipApiStatus(e.target.checked);
        });
    }

    async checkStatus() {
        try {
            const response = await fetch('/api/status');
            const status = await response.json();
            
            this.updateStatusBadges(status);
            this.updateStartButton(status);
            
        } catch (error) {
            console.error('Failed to check status:', error);
            this.addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: '❌ Failed to check system status',
                level: 'error'
            });
        }
    }

    updateStatusBadges(status) {
        const policyStatus = document.getElementById('policy-status');
        const questionnaireStatus = document.getElementById('questionnaire-status');
        const apiKeyStatus = document.getElementById('api-key-status');

        // Policy file status
        if (status.policy_exists) {
            policyStatus.textContent = 'Found';
            policyStatus.className = 'badge bg-success';
        } else {
            policyStatus.textContent = 'Missing';
            policyStatus.className = 'badge bg-danger';
        }

        // Questionnaire status
        if (status.questionnaire_exists) {
            questionnaireStatus.textContent = 'Found';
            questionnaireStatus.className = 'badge bg-success';
        } else {
            questionnaireStatus.textContent = 'Missing';
            questionnaireStatus.className = 'badge bg-danger';
        }

        // API key status
        if (status.api_key_configured) {
            apiKeyStatus.textContent = status.skip_api ? 'Not Required' : 'Configured';
            apiKeyStatus.className = 'badge bg-success';
        } else {
            apiKeyStatus.textContent = 'Missing';
            apiKeyStatus.className = 'badge bg-danger';
        }

        this.automationRunning = status.automation_running;
    }

    updateStartButton(status) {
        const startButton = document.getElementById('start-automation');
        const controlsDiv = document.getElementById('automation-controls');
        
        const canStart = status.policy_exists && 
                        status.questionnaire_exists && 
                        (status.api_key_configured || status.skip_api) &&
                        !this.automationRunning;

        startButton.disabled = !canStart;
        
        if (this.automationRunning) {
            startButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Running...';
            startButton.disabled = true;
            controlsDiv.style.display = 'block';
        } else {
            startButton.innerHTML = '<i class="fas fa-play me-2"></i>Start Policy Automation';
            controlsDiv.style.display = 'none';
        }
    }

    async startAutomation() {
        const skipApi = document.getElementById('skipApiCheck').checked;
        
        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ skip_api: skipApi })
            });

            if (response.ok) {
                this.automationRunning = true;
                this.updateStartButton({ 
                    policy_exists: true, 
                    questionnaire_exists: true, 
                    api_key_configured: true 
                });
                this.resetProgress();
                this.hideDownloadSection();
            } else {
                const error = await response.json();
                this.addLogEntry({
                    timestamp: new Date().toLocaleTimeString(),
                    message: `❌ Failed to start automation: ${error.error}`,
                    level: 'error'
                });
            }
        } catch (error) {
            console.error('Failed to start automation:', error);
            this.addLogEntry({
                timestamp: new Date().toLocaleTimeString(),
                message: '❌ Failed to start automation: Network error',
                level: 'error'
            });
        }
    }

    async stopAutomation() {
        try {
            const response = await fetch('/api/stop', {
                method: 'POST'
            });

            if (response.ok) {
                this.automationRunning = false;
                this.updateStartButton({ 
                    policy_exists: true, 
                    questionnaire_exists: true, 
                    api_key_configured: true 
                });
            }
        } catch (error) {
            console.error('Failed to stop automation:', error);
        }
    }

    addLogEntry(data) {
        const logContainer = document.getElementById('log-container');
        const logEntry = document.createElement('div');
        
        logEntry.className = `log-entry ${data.level}`;
        logEntry.innerHTML = `
            <div class="log-timestamp">${data.timestamp}</div>
            <div class="log-message">${this.escapeHtml(data.message)}</div>
        `;
        
        logContainer.appendChild(logEntry);
        
        this.logCount++;
        document.getElementById('log-count').textContent = `${this.logCount} logs`;
        
        // Auto-scroll to bottom
        this.scrollToBottom();
    }

    updateProgress(data) {
        const progressBar = document.getElementById('progress-bar');
        const steps = document.querySelectorAll('.step-item');
        
        // Update progress bar
        progressBar.style.width = `${data.progress}%`;
        
        // Update step status
        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            step.classList.remove('active', 'completed', 'error');
            
            if (stepNumber < data.step) {
                step.classList.add('completed');
            } else if (stepNumber === data.step) {
                step.classList.add(data.status);
            }
        });

        // Check if automation is complete
        if (data.step === 5 && data.status === 'completed') {
            this.automationRunning = false;
            this.updateStartButton({ 
                policy_exists: true, 
                questionnaire_exists: true, 
                api_key_configured: true 
            });
        }
    }

    resetProgress() {
        const progressBar = document.getElementById('progress-bar');
        const steps = document.querySelectorAll('.step-item');
        
        progressBar.style.width = '0%';
        steps.forEach(step => {
            step.classList.remove('active', 'completed', 'error');
        });
    }

    showDownloadLinks(files) {
        const downloadSection = document.getElementById('download-section');
        const downloadLinks = document.getElementById('download-links');
        
        downloadLinks.innerHTML = '';
        
        files.forEach(file => {
            const downloadItem = document.createElement('div');
            downloadItem.className = 'download-item';
            downloadItem.innerHTML = `
                <div class="download-info">
                    <div class="download-name">${file.name}</div>
                    <div class="download-size">${file.size}</div>
                </div>
                <a href="/api/download/${encodeURIComponent(file.path)}" 
                   class="btn btn-primary btn-sm" download>
                    <i class="fas fa-download me-1"></i>Download
                </a>
            `;
            downloadLinks.appendChild(downloadItem);
        });
        
        downloadSection.style.display = 'block';
    }

    hideDownloadSection() {
        document.getElementById('download-section').style.display = 'none';
    }

    clearLogs() {
        const logContainer = document.getElementById('log-container');
        const welcomeLog = logContainer.querySelector('.log-entry.welcome');
        
        // Clear all logs except welcome message
        logContainer.innerHTML = '';
        if (welcomeLog) {
            logContainer.appendChild(welcomeLog.cloneNode(true));
            this.logCount = 1;
        } else {
            this.logCount = 0;
        }
        
        document.getElementById('log-count').textContent = `${this.logCount} logs`;
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        const badge = statusElement.querySelector('.badge');
        
        if (connected) {
            badge.className = 'badge bg-success';
            badge.innerHTML = '<i class="fas fa-wifi me-1"></i>Connected';
        } else {
            badge.className = 'badge bg-danger';
            badge.innerHTML = '<i class="fas fa-wifi me-1"></i>Disconnected';
        }
    }

    updateSkipApiStatus(enabled) {
        const statusBadge = document.getElementById('skip-api-status');
        statusBadge.textContent = enabled ? 'Yes' : 'No';
        statusBadge.className = enabled ? 'badge bg-warning' : 'badge bg-info';
        
        // Recheck status to update start button
        this.checkStatus();
    }

    setupAutoScroll() {
        const logContainer = document.getElementById('log-container');
        this.autoScrollEnabled = true;
        
        // Disable auto-scroll when user scrolls up
        logContainer.addEventListener('scroll', () => {
            const { scrollTop, scrollHeight, clientHeight } = logContainer;
            this.autoScrollEnabled = scrollTop + clientHeight >= scrollHeight - 5;
        });
    }

    scrollToBottom() {
        if (this.autoScrollEnabled) {
            const logContainer = document.getElementById('log-container');
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new PolicyAutomationDashboard();
    
    // Periodic status check every 30 seconds
    setInterval(() => {
        if (!window.dashboard.automationRunning) {
            window.dashboard.checkStatus();
        }
    }, 30000);
});