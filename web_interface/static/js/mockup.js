// Web Scraper Interface Mockup JavaScript
// This file provides interactive functionality for the mockup

document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const urlInput = document.getElementById('url-input');
    const startButton = document.getElementById('start-scraping');
    const dryRunButton = document.getElementById('dry-run');
    const clearButton = document.getElementById('clear-form');
    const maxWorkersSlider = document.getElementById('max-workers');
    const delaySlider = document.getElementById('delay');
    const workersValue = document.getElementById('workers-value');
    const delayValue = document.getElementById('delay-value');
    const progressPanel = document.querySelector('.progress-panel');
    const configPanel = document.querySelector('.config-panel');

    // URL validation function
    function isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    // Update button states based on URL input
    function updateButtonStates() {
        const url = urlInput.value.trim();
        const isValid = isValidUrl(url);
        
        startButton.disabled = !isValid;
        dryRunButton.disabled = !isValid;
        
        if (isValid) {
            urlInput.style.borderColor = '#059669';
            urlInput.style.backgroundColor = '#f0fdf4';
        } else if (url.length > 0) {
            urlInput.style.borderColor = '#dc2626';
            urlInput.style.backgroundColor = '#fef2f2';
        } else {
            urlInput.style.borderColor = '#d1d5db';
            urlInput.style.backgroundColor = 'white';
        }
    }

    // URL input event listener
    urlInput.addEventListener('input', updateButtonStates);
    urlInput.addEventListener('blur', updateButtonStates);

    // Range slider updates
    maxWorkersSlider.addEventListener('input', function() {
        workersValue.textContent = this.value;
    });

    delaySlider.addEventListener('input', function() {
        delayValue.textContent = parseFloat(this.value).toFixed(1);
    });

    // Clear form functionality
    clearButton.addEventListener('click', function() {
        urlInput.value = '';
        document.getElementById('ignore-robots').checked = false;
        document.getElementById('max-depth').value = '1';
        document.getElementById('download-images').checked = true;
        document.getElementById('download-videos').checked = true;
        document.getElementById('download-text').checked = true;
        maxWorkersSlider.value = '5';
        delaySlider.value = '1.0';
        workersValue.textContent = '5';
        delayValue.textContent = '1.0';
        document.getElementById('user-agent').value = 'WebScraper/1.0';
        updateButtonStates();
        
        // Reset input styling
        urlInput.style.borderColor = '#d1d5db';
        urlInput.style.backgroundColor = 'white';
    });

    // Start scraping simulation
    startButton.addEventListener('click', function() {
        if (!isValidUrl(urlInput.value.trim())) {
            alert('Please enter a valid URL');
            return;
        }
        
        // Show progress panel
        progressPanel.style.display = 'block';
        progressPanel.scrollIntoView({ behavior: 'smooth' });
        
        // Disable form
        startButton.disabled = true;
        startButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';
        
        // Simulate progress
        simulateProgress();
    });

    // Dry run simulation
    dryRunButton.addEventListener('click', function() {
        if (!isValidUrl(urlInput.value.trim())) {
            alert('Please enter a valid URL');
            return;
        }
        
        const url = urlInput.value.trim();
        const depth = document.getElementById('max-depth').value;
        const respectRobots = !document.getElementById('ignore-robots').checked;
        
        let message = `Dry Run Results for: ${url}\n\n`;
        message += `Max Depth: ${depth}\n`;
        message += `Respect robots.txt: ${respectRobots ? 'Yes' : 'No'}\n\n`;
        message += `This would scrape:\n`;
        message += `• Main page content\n`;
        if (depth > 1) {
            message += `• Links up to ${depth} levels deep\n`;
        }
        message += `• Images, videos, and text (based on your selections)\n\n`;
        message += `No files would be downloaded in dry run mode.`;
        
        alert(message);
    });

    // Progress simulation function
    function simulateProgress() {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        const statusMessage = document.querySelector('.status-message');
        const statValues = document.querySelectorAll('.stat-value');
        
        let progress = 0;
        const interval = setInterval(function() {
            progress += Math.random() * 15;
            if (progress > 100) progress = 100;
            
            progressFill.style.width = progress + '%';
            progressText.textContent = Math.round(progress) + '% Complete';
            
            // Update stats
            const urls = Math.round((progress / 100) * 150);
            const files = Math.round((progress / 100) * 120);
            const size = ((progress / 100) * 67.3).toFixed(1);
            const timeElapsed = Math.round((progress / 100) * 180);
            const minutes = Math.floor(timeElapsed / 60);
            const seconds = timeElapsed % 60;
            
            statValues[0].textContent = urls;
            statValues[1].textContent = files;
            statValues[2].textContent = size + ' MB';
            statValues[3].textContent = minutes + 'm ' + seconds + 's';
            
            // Update status message
            const pages = [
                'https://example.com/',
                'https://example.com/about',
                'https://example.com/products',
                'https://example.com/contact',
                'https://example.com/blog'
            ];
            const randomPage = pages[Math.floor(Math.random() * pages.length)];
            statusMessage.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Processing: ${randomPage}`;
            
            if (progress >= 100) {
                clearInterval(interval);
                statusMessage.innerHTML = '<i class="fas fa-check-circle" style="color: #059669;"></i> Scraping completed successfully!';
                
                // Re-enable start button
                setTimeout(function() {
                    startButton.disabled = false;
                    startButton.innerHTML = '<i class="fas fa-play"></i> Start Scraping';
                    updateButtonStates();
                }, 2000);
                
                // Show results panel
                setTimeout(function() {
                    document.querySelector('.results-panel').scrollIntoView({ behavior: 'smooth' });
                }, 1500);
            }
        }, 500);
    }

    // Checkbox styling updates
    document.querySelectorAll('.checkbox-input').forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            // Add visual feedback or validation here if needed
        });
    });

    // Advanced settings toggle animation
    const advancedSettings = document.querySelector('.advanced-settings');
    advancedSettings.addEventListener('toggle', function() {
        if (this.open) {
            this.querySelector('.advanced-content').style.animation = 'slideDown 0.3s ease';
        }
    });

    // Add slide down animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);

    // Re-run button functionality for history items
    document.querySelectorAll('.job-item .btn').forEach(function(button) {
        if (button.textContent.includes('Re-run')) {
            button.addEventListener('click', function() {
                const jobItem = this.closest('.job-item');
                const jobUrl = jobItem.querySelector('.job-url').textContent;
                
                if (confirm(`Re-run scraping job for: ${jobUrl}?`)) {
                    urlInput.value = jobUrl;
                    updateButtonStates();
                    urlInput.scrollIntoView({ behavior: 'smooth' });
                    
                    // Highlight the URL input
                    urlInput.style.borderColor = '#2563eb';
                    urlInput.style.backgroundColor = '#eff6ff';
                    setTimeout(function() {
                        urlInput.style.borderColor = '#059669';
                        urlInput.style.backgroundColor = '#f0fdf4';
                    }, 1000);
                }
            });
        }
    });

    // Download and view buttons
    document.querySelectorAll('.results-actions .btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const action = this.textContent.trim();
            if (action.includes('Download')) {
                alert('Download functionality would be implemented here.\nFiles would be packaged as a ZIP file.');
            } else if (action.includes('View Files')) {
                alert('File browser functionality would be implemented here.\nUsers could browse downloaded files in a tree view.');
            } else if (action.includes('View Log')) {
                alert('Log viewer functionality would be implemented here.\nDetailed scraping logs would be displayed.');
            }
        });
    });

    // Cancel job functionality
    document.getElementById('cancel-job')?.addEventListener('click', function() {
        if (confirm('Are you sure you want to cancel the current scraping job?')) {
            alert('Scraping job cancelled.\nPartial results would be saved.');
            progressPanel.style.display = 'none';
            startButton.disabled = false;
            startButton.innerHTML = '<i class="fas fa-play"></i> Start Scraping';
            updateButtonStates();
        }
    });

    // Clear history functionality
    const clearHistoryButton = document.getElementById('clear-history');
    const historyContent = document.querySelector('.history-content');
    const historyEmpty = document.querySelector('.history-empty');

    clearHistoryButton.addEventListener('click', function() {
        const jobItems = document.querySelectorAll('.job-item');
        
        if (jobItems.length === 0) {
            alert('No history to clear.');
            return;
        }
        
        // Custom confirmation dialog
        const confirmDialog = createConfirmDialog(
            'Clear Scraping History',
            `Are you sure you want to clear all ${jobItems.length} scraping job(s) from your history?`,
            'This action cannot be undone.',
            'Clear History',
            'Cancel'
        );
        
        confirmDialog.onConfirm = function() {
            // Animate removal of job items
            jobItems.forEach((item, index) => {
                setTimeout(() => {
                    item.style.transition = 'all 0.3s ease';
                    item.style.transform = 'translateX(-100%)';
                    item.style.opacity = '0';
                    
                    setTimeout(() => {
                        item.remove();
                        
                        // Show empty state after last item is removed
                        if (index === jobItems.length - 1) {
                            setTimeout(() => {
                                showEmptyHistoryState();
                            }, 100);
                        }
                    }, 300);
                }, index * 100);
            });
            
            // Update clear button state
            setTimeout(() => {
                clearHistoryButton.disabled = true;
                clearHistoryButton.innerHTML = '<i class="fas fa-check"></i> Cleared';
                clearHistoryButton.classList.remove('btn-danger');
                clearHistoryButton.classList.add('btn-secondary');
                
                // Reset button after delay
                setTimeout(() => {
                    clearHistoryButton.disabled = false;
                    clearHistoryButton.innerHTML = '<i class="fas fa-trash"></i> Clear History';
                    clearHistoryButton.classList.remove('btn-secondary');
                    clearHistoryButton.classList.add('btn-danger');
                }, 2000);
            }, (jobItems.length * 100) + 500);
        };
        
        document.body.appendChild(confirmDialog.element);
        confirmDialog.show();
    });

    function showEmptyHistoryState() {
        const historyContent = document.querySelector('.history-content');
        const historyEmpty = document.querySelector('.history-empty');
        
        if (historyContent && historyEmpty) {
            historyContent.style.display = 'none';
            historyEmpty.style.display = 'block';
            historyEmpty.style.animation = 'fadeIn 0.5s ease';
        }
    }

    function createConfirmDialog(title, message, subtitle, confirmText, cancelText) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        
        const modal = document.createElement('div');
        modal.className = 'modal-dialog';
        
        modal.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title">
                    <i class="fas fa-exclamation-triangle" style="color: var(--warning-color);"></i>
                    ${title}
                </h3>
            </div>
            <div class="modal-body">
                <p class="modal-message">${message}</p>
                ${subtitle ? `<p class="modal-subtitle">${subtitle}</p>` : ''}
            </div>
            <div class="modal-footer">
                <button class="btn btn-danger modal-confirm">${confirmText}</button>
                <button class="btn btn-secondary modal-cancel">${cancelText}</button>
            </div>
        `;
        
        overlay.appendChild(modal);
        
        const confirmBtn = modal.querySelector('.modal-confirm');
        const cancelBtn = modal.querySelector('.modal-cancel');
        
        const dialog = {
            element: overlay,
            onConfirm: null,
            onCancel: null,
            show: function() {
                overlay.style.display = 'flex';
                setTimeout(() => {
                    overlay.classList.add('show');
                }, 10);
            },
            hide: function() {
                overlay.classList.remove('show');
                setTimeout(() => {
                    overlay.remove();
                }, 300);
            }
        };
        
        confirmBtn.addEventListener('click', () => {
            if (dialog.onConfirm) dialog.onConfirm();
            dialog.hide();
        });
        
        cancelBtn.addEventListener('click', () => {
            if (dialog.onCancel) dialog.onCancel();
            dialog.hide();
        });
        
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                if (dialog.onCancel) dialog.onCancel();
                dialog.hide();
            }
        });
        
        return dialog;
    }

    // Initialize the interface
    updateButtonStates();
    
    // Add animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);

    // Add some helpful tooltips
    const tooltips = {
        'max-depth': 'Controls how many levels deep the scraper will follow links from the starting URL',
        'ignore-robots': 'When checked, the scraper will ignore robots.txt restrictions (use responsibly)',
        'max-workers': 'Number of concurrent download threads (more workers = faster but more resource intensive)',
        'delay': 'Delay between requests to be respectful to the target server'
    };
    
    Object.keys(tooltips).forEach(function(id) {
        const element = document.getElementById(id);
        if (element) {
            element.title = tooltips[id];
        }
    });
});