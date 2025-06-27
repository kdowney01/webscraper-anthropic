/**
 * Web Scraper Interface JavaScript
 * Handles form submission, WebSocket communication, and UI updates
 */

class WebScraperApp {
    constructor() {
        this.socket = null;
        this.currentJobId = null;
        this.jobs = [];
        this.history = [];
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.bindEventListeners();
        this.loadJobHistory();
        this.setupFormValidation();
    }
    
    initializeSocket() {
        // Skip Socket.IO - use polling instead
        console.log('Using polling for job updates instead of Socket.IO');
        this.pollInterval = null;
    }
    
    bindEventListeners() {
        // Form submission
        document.getElementById('scrape-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startScraping();
        });
        
        // Dry run
        document.getElementById('dry-run').addEventListener('click', () => {
            this.performDryRun();
        });
        
        // Clear form
        document.getElementById('clear-form').addEventListener('click', () => {
            this.clearForm();
        });
        
        // Clear history
        document.getElementById('clear-history').addEventListener('click', () => {
            this.clearHistory();
        });
        
        // Cancel job
        document.getElementById('cancel-job').addEventListener('click', () => {
            this.cancelJob();
        });
        
        // Range sliders
        document.getElementById('max-workers').addEventListener('input', (e) => {
            document.getElementById('workers-value').textContent = e.target.value;
        });
        
        document.getElementById('delay').addEventListener('input', (e) => {
            document.getElementById('delay-value').textContent = parseFloat(e.target.value).toFixed(1);
        });
        
        // URL validation
        document.getElementById('url-input').addEventListener('input', () => {
            this.validateUrl();
        });
        
        document.getElementById('url-input').addEventListener('blur', () => {
            this.validateUrl();
        });
    }
    
    setupFormValidation() {
        this.validateUrl();
    }
    
    validateUrl() {
        const urlInput = document.getElementById('url-input');
        const urlError = document.getElementById('url-error');
        const startButton = document.getElementById('start-scraping');
        const dryRunButton = document.getElementById('dry-run');
        
        const url = urlInput.value.trim();
        
        if (!url) {
            urlInput.classList.remove('error', 'success');
            urlError.classList.remove('show');
            startButton.disabled = true;
            dryRunButton.disabled = true;
            return;
        }
        
        if (this.isValidUrl(url)) {
            urlInput.classList.remove('error');
            urlInput.classList.add('success');
            urlError.classList.remove('show');
            startButton.disabled = false;
            dryRunButton.disabled = false;
        } else {
            urlInput.classList.remove('success');
            urlInput.classList.add('error');
            urlError.textContent = 'Please enter a valid HTTP or HTTPS URL';
            urlError.classList.add('show');
            startButton.disabled = true;
            dryRunButton.disabled = true;
        }
    }
    
    isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }
    
    getFormData() {
        const form = document.getElementById('scrape-form');
        const formData = new FormData(form);
        
        return {
            url: formData.get('url'),
            max_depth: parseInt(formData.get('max_depth')),
            ignore_robots: formData.has('ignore_robots'),
            download_images: formData.has('download_images'),
            download_videos: formData.has('download_videos'),
            download_text: formData.has('download_text'),
            max_workers: parseInt(formData.get('max_workers')),
            delay: parseFloat(formData.get('delay')),
            user_agent: formData.get('user_agent') || 'WebScraper/1.0'
        };
    }
    
    async startScraping() {
        try {
            const data = this.getFormData();
            
            if (!this.isValidUrl(data.url)) {
                this.showNotification('Please enter a valid URL', 'error');
                return;
            }
            
            // Disable form
            this.setFormEnabled(false);
            
            // Show progress panel
            this.showProgressPanel();
            
            // Start scraping
            const response = await fetch('/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.currentJobId = result.job_id;
                console.log('🚀 Job started with ID:', this.currentJobId);
                console.log('📡 Starting progress polling...');
                this.startPolling();
                this.showNotification('Scraping started successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to start scraping');
            }
            
        } catch (error) {
            console.error('Error starting scraping:', error);
            this.showNotification(error.message, 'error');
            this.setFormEnabled(true);
            this.hideProgressPanel();
        }
    }
    
    async performDryRun() {
        try {
            const data = this.getFormData();
            
            if (!this.isValidUrl(data.url)) {
                this.showNotification('Please enter a valid URL', 'error');
                return;
            }
            
            const response = await fetch('/api/dry-run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showDryRunResults(result);
            } else {
                throw new Error(result.error || 'Dry run failed');
            }
            
        } catch (error) {
            console.error('Error performing dry run:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    showDryRunResults(results) {
        const message = `
Dry Run Results for: ${results.url}

Domain: ${results.domain}
Max Depth: ${results.max_depth}
Respect robots.txt: ${results.respect_robots ? 'Yes' : 'No'}

Estimated content:
• ${results.estimated_pages} pages
• ${results.estimated_images} images
• ${results.estimated_videos} videos
• ${results.estimated_total_files} total files

No files would be downloaded in dry run mode.
        `.trim();
        
        alert(message);
    }
    
    async cancelJob() {
        if (!this.currentJobId) return;
        
        try {
            const response = await fetch(`/api/jobs/${this.currentJobId}/cancel`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.stopPolling();
                this.showNotification('Job cancelled successfully', 'info');
            } else {
                throw new Error(result.error || 'Failed to cancel job');
            }
            
        } catch (error) {
            console.error('Error cancelling job:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    clearForm() {
        document.getElementById('scrape-form').reset();
        document.getElementById('workers-value').textContent = '5';
        document.getElementById('delay-value').textContent = '1.0';
        this.validateUrl();
        this.showNotification('Form cleared', 'info');
    }
    
    async clearHistory() {
        try {
            const confirmed = confirm('Are you sure you want to clear all scraping history? This action cannot be undone.');
            
            if (!confirmed) return;
            
            const response = await fetch('/api/history/clear', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.history = [];
                this.renderHistory();
                this.showNotification('History cleared successfully', 'success');
            } else {
                throw new Error(result.error || 'Failed to clear history');
            }
            
        } catch (error) {
            console.error('Error clearing history:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    startPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
        
        console.log('⏰ Starting job status polling...');
        this.pollInterval = setInterval(() => {
            this.pollJobStatus();
        }, 1000); // Poll every second
        
        // Also poll immediately
        this.pollJobStatus();
    }
    
    stopPolling() {
        if (this.pollInterval) {
            console.log('⏹️ Stopping job status polling');
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    async pollJobStatus() {
        if (!this.currentJobId) {
            this.stopPolling();
            return;
        }
        
        try {
            const response = await fetch(`/api/status/${this.currentJobId}`);
            const jobData = await response.json();
            
            if (response.ok) {
                console.log('📊 Polling update:', jobData.status, jobData.progress + '%', jobData.status_message);
                this.updateProgress(jobData);
                
                // Check if job is finished
                if (jobData.status === 'completed') {
                    console.log('✅ Job completed successfully!');
                    this.stopPolling();
                    
                    // Ensure progress shows 100%
                    jobData.progress = 100;
                    this.updateProgress(jobData);
                    
                    // Show completion after a brief delay to see 100%
                    setTimeout(() => {
                        this.showResults(jobData);
                        this.setFormEnabled(true);
                        this.currentJobId = null;
                        this.loadJobHistory();
                    }, 1000);
                    
                } else if (jobData.status === 'failed') {
                    console.log('❌ Job failed:', jobData.error_message);
                    this.stopPolling();
                    this.showError(jobData.error_message);
                    this.setFormEnabled(true);
                    this.hideProgressPanel();
                    this.currentJobId = null;
                    this.loadJobHistory();
                } else if (jobData.status === 'cancelled') {
                    console.log('⚠️ Job cancelled');
                    this.stopPolling();
                    this.hideProgressPanel();
                    this.setFormEnabled(true);
                    this.currentJobId = null;
                    this.loadJobHistory();
                }
            } else {
                console.error('❌ Error polling job status:', jobData);
                if (response.status === 404) {
                    console.log('Job not found, checking history...');
                    // Job might have moved to history, check there
                    await this.checkJobInHistory();
                }
            }
        } catch (error) {
            console.error('❌ Error polling job status:', error);
        }
    }
    
    async checkJobInHistory() {
        try {
            const response = await fetch('/api/jobs');
            const data = await response.json();
            
            if (response.ok && data.history) {
                const completedJob = data.history.find(job => job.id === this.currentJobId);
                if (completedJob) {
                    console.log('✅ Found completed job in history:', completedJob.status);
                    this.stopPolling();
                    
                    if (completedJob.status === 'completed') {
                        // Ensure progress shows 100%
                        completedJob.progress = 100;
                        this.updateProgress(completedJob);
                        
                        setTimeout(() => {
                            this.showResults(completedJob);
                            this.setFormEnabled(true);
                            this.currentJobId = null;
                            this.loadJobHistory();
                        }, 1000);
                    } else {
                        this.setFormEnabled(true);
                        this.currentJobId = null;
                        this.loadJobHistory();
                    }
                } else {
                    // Job really not found
                    this.stopPolling();
                    this.setFormEnabled(true);
                    this.currentJobId = null;
                }
            }
        } catch (error) {
            console.error('❌ Error checking job history:', error);
            this.stopPolling();
            this.setFormEnabled(true);
            this.currentJobId = null;
        }
    }

    handleJobUpdate(data) {
        // Legacy Socket.IO handler - not used with polling
        console.log('Socket.IO job update (not used):', data);
    }
    
    updateProgress(jobData) {
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const statusMessage = document.getElementById('status-message');
        
        // Update progress bar
        const progress = jobData.progress || 0;
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `${Math.round(progress)}% Complete`;
        
        // Update status message
        let message = jobData.status_message || 'Processing...';
        let icon = 'fas fa-spinner fa-spin';
        
        if (jobData.status === 'running') {
            if (jobData.status_message) {
                message = jobData.status_message;
            } else {
                message = `Scraping: ${jobData.url}`;
            }
        } else if (jobData.status === 'completed') {
            message = jobData.status_message || 'Scraping completed successfully!';
            icon = 'fas fa-check-circle';
        } else if (jobData.status === 'failed') {
            message = jobData.status_message || `Error: ${jobData.error_message}`;
            icon = 'fas fa-exclamation-triangle';
        } else if (jobData.status === 'pending') {
            message = jobData.status_message || 'Job pending...';
            icon = 'fas fa-clock';
        }
        
        statusMessage.innerHTML = `<i class="${icon}"></i> ${message}`;
        
        // Update stats
        const stats = jobData.stats || {};
        document.getElementById('stat-urls').textContent = stats.urls_processed || 0;
        document.getElementById('stat-files').textContent = stats.files_downloaded || 0;
        document.getElementById('stat-size').textContent = this.formatFileSize(stats.total_size || 0);
        document.getElementById('stat-errors').textContent = stats.errors || 0;
        
        // Debug logging
        console.log('Job update received:', {
            job_id: jobData.id,
            status: jobData.status,
            progress: progress,
            status_message: jobData.status_message,
            stats: stats
        });
    }
    
    showResults(jobData) {
        const resultsPanel = document.getElementById('results-panel');
        const resultsSummary = document.getElementById('results-summary');
        const resultsActions = document.getElementById('results-actions');
        
        const stats = jobData.stats || {};
        
        // Show results summary
        resultsSummary.innerHTML = `
            <div class="success-indicator">
                <i class="fas fa-check-circle"></i>
                <span>Scraping completed successfully!</span>
            </div>
            
            <div class="results-stats">
                <div class="result-item success">
                    <i class="fas fa-download"></i>
                    <span>${stats.files_downloaded || 0} files downloaded</span>
                </div>
                <div class="result-item warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>${stats.errors || 0} errors</span>
                </div>
                <div class="result-item success">
                    <i class="fas fa-chart-bar"></i>
                    <span>${stats.urls_processed || 0} URLs processed</span>
                </div>
            </div>
        `;
        
        // Show results actions
        resultsActions.innerHTML = `
            <button class="btn btn-success" onclick="app.downloadResults('${jobData.id}')">
                <i class="fas fa-download"></i> Download Results (ZIP)
            </button>
            <button class="btn btn-info" onclick="app.viewFiles('${jobData.id}')">
                <i class="fas fa-folder-open"></i> View Files
            </button>
            <button class="btn btn-secondary" onclick="app.viewLog('${jobData.id}')">
                <i class="fas fa-file-alt"></i> View Log
            </button>
        `;
        
        resultsPanel.style.display = 'block';
        resultsPanel.scrollIntoView({ behavior: 'smooth' });
    }
    
    showError(errorMessage) {
        this.showNotification(`Scraping failed: ${errorMessage}`, 'error');
    }
    
    async downloadResults(jobId) {
        try {
            const response = await fetch(`/api/jobs/${jobId}/download`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `scrape_results_${jobId.slice(0, 8)}.zip`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showNotification('Download started', 'success');
            } else {
                const result = await response.json();
                throw new Error(result.error || 'Download failed');
            }
            
        } catch (error) {
            console.error('Error downloading results:', error);
            this.showNotification(error.message, 'error');
        }
    }
    
    viewFiles(jobId) {
        this.showNotification('File browser functionality would be implemented here', 'info');
    }
    
    viewLog(jobId) {
        this.showNotification('Log viewer functionality would be implemented here', 'info');
    }
    
    async loadJobHistory() {
        try {
            console.log('Loading job history...');
            const response = await fetch('/api/jobs');
            const data = await response.json();
            
            if (response.ok) {
                this.jobs = data.active_jobs || [];
                this.history = data.history || [];
                console.log('Job history loaded:', {
                    active_jobs: this.jobs.length,
                    history: this.history.length,
                    data: data
                });
                this.renderHistory();
            } else {
                console.error('Failed to load job history:', data);
            }
            
        } catch (error) {
            console.error('Error loading job history:', error);
        }
    }
    
    renderHistory() {
        const historyContent = document.getElementById('history-content');
        const historyEmpty = document.getElementById('history-empty');
        
        console.log('Rendering history:', this.history.length, 'items');
        
        if (this.history.length === 0) {
            console.log('No history items, showing empty state');
            historyContent.style.display = 'none';
            historyEmpty.style.display = 'block';
            return;
        }
        
        historyContent.style.display = 'block';
        historyEmpty.style.display = 'none';
        
        historyContent.innerHTML = this.history.map(job => {
            const date = new Date(job.updated_at);
            const timeAgo = this.getTimeAgo(date);
            const stats = job.stats || {};
            
            let metaText = timeAgo;
            if (job.status === 'completed') {
                metaText += ` • ${stats.files_downloaded || 0} files`;
                if (stats.total_size) {
                    metaText += ` • ${this.formatFileSize(stats.total_size)}`;
                }
            } else if (job.error_message) {
                metaText += ` • ${job.error_message}`;
            }
            
            return `
                <div class="job-item">
                    <div class="job-info">
                        <div class="job-url">${job.url}</div>
                        <div class="job-meta">${metaText}</div>
                    </div>
                    <div class="job-status">
                        <span class="status-badge ${job.status}">${this.capitalizeFirst(job.status)}</span>
                        <button class="btn btn-small btn-secondary" onclick="app.rerunJob('${job.url}')">
                            <i class="fas fa-redo"></i> Re-run
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    rerunJob(url) {
        document.getElementById('url-input').value = url;
        this.validateUrl();
        document.getElementById('url-input').scrollIntoView({ behavior: 'smooth' });
        this.showNotification('URL loaded for re-run', 'info');
    }
    
    showProgressPanel() {
        document.getElementById('progress-panel').style.display = 'block';
        document.getElementById('results-panel').style.display = 'none';
        
        // Reset progress
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('progress-text').textContent = '0% Complete';
        document.getElementById('status-message').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initializing...';
        
        // Reset stats
        document.getElementById('stat-urls').textContent = '0';
        document.getElementById('stat-files').textContent = '0';
        document.getElementById('stat-size').textContent = '0 B';
        document.getElementById('stat-errors').textContent = '0';
    }
    
    hideProgressPanel() {
        document.getElementById('progress-panel').style.display = 'none';
    }
    
    setFormEnabled(enabled) {
        const form = document.getElementById('scrape-form');
        const inputs = form.querySelectorAll('input, select, button');
        
        inputs.forEach(input => {
            input.disabled = !enabled;
        });
        
        if (enabled) {
            this.validateUrl();
        }
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        
        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let unitIndex = 0;
        let size = bytes;
        
        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }
        
        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }
    
    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    }
    
    capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new WebScraperApp();
});