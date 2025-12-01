// Global variables
let currentPage = 1;
const perPage = 20;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    loadRefreshStatus();
    loadJobs();
    setupEventListeners();
    loadSources();
    updateSourceFormLabels(); // Initialize form labels
    
    // Update status every 30 seconds
    setInterval(loadRefreshStatus, 30000);
});

// Setup event listeners
function setupEventListeners() {
    // Search inputs
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentPage = 1;
            loadJobs();
        }
    });
    
    document.getElementById('location-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentPage = 1;
            loadJobs();
        }
    });
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const filterType = this.dataset.filter;
            
            if (filterType === 'details') {
                // Toggle details visibility for all job cards
                toggleAllJobDescriptions(this);
                return; // Don't reload jobs or change active state
            }
            
            // Toggle active state for other filters
            document.querySelectorAll('.filter-btn').forEach(b => {
                if (b.dataset.filter !== 'details') {
                    b.classList.remove('active');
                }
            });
            this.classList.add('active');
            
            currentPage = 1;
            loadJobs();
        });
    });
    
    // Level filter dropdown
    const levelFilter = document.getElementById('level-filter');
    if (levelFilter) {
        levelFilter.addEventListener('change', function() {
            currentPage = 1;
            loadJobs();
        });
    }
    
    // Pay filter dropdown
    const payFilter = document.getElementById('pay-filter');
    if (payFilter) {
        payFilter.addEventListener('change', function() {
            currentPage = 1;
            loadJobs();
        });
    }
    
    // Refresh button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshNow);
    }
    
    // Pagination
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadJobs();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        currentPage++;
        loadJobs();
    });
    
    // Add source form
    const addSourceForm = document.getElementById('add-source-form');
    if (addSourceForm) {
        addSourceForm.addEventListener('submit', addSource);
    }
    
    // Admin toggle
    const adminToggle = document.getElementById('admin-toggle');
    if (adminToggle) {
        adminToggle.addEventListener('click', () => {
            const panel = document.getElementById('admin-panel');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        });
    }
}

// Load refresh status
async function loadRefreshStatus() {
    try {
        const response = await fetch('/api/refresh-status');
        const data = await response.json();
        
        // Update header counts
        const jobsCountHeader = document.getElementById('jobs-count-header');
        if (jobsCountHeader) {
            jobsCountHeader.textContent = data.jobs_count || 0;
        }
        
        // Update companies count (unique companies from jobs)
        const companiesCount = document.getElementById('companies-count');
        if (companiesCount) {
            companiesCount.textContent = data.companies_count || 0;
        }
        
        // Update admin panel status
        const lastRefresh = document.getElementById('last-refresh');
        if (lastRefresh) {
            if (data.last_refresh) {
                const date = new Date(data.last_refresh);
                lastRefresh.textContent = date.toLocaleString('en-US');
            } else {
                lastRefresh.textContent = 'Never';
            }
        }
        
        const sourcesCount = document.getElementById('sources-count');
        if (sourcesCount) {
            sourcesCount.textContent = data.sources_count || 0;
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

// Load jobs list
async function loadJobs() {
    const container = document.getElementById('jobs-container');
    if (!container) {
        console.error('jobs-container element not found');
        return;
    }
    
    container.innerHTML = '<div class="loading">Loading...</div>';
    
    const searchInput = document.getElementById('search-input');
    const locationInput = document.getElementById('location-input');
    const levelFilter = document.getElementById('level-filter');
    const payFilter = document.getElementById('pay-filter');
    
    const search = searchInput ? searchInput.value.trim() : '';
    const location = locationInput ? locationInput.value.trim() : '';
    const level = levelFilter ? levelFilter.value : '';
    const pay = payFilter ? payFilter.value : '';
    
    try {
        // Build search parameters
        const params = new URLSearchParams({
            page: currentPage,
            per_page: perPage,
            level: level
        });
        
        // Add search, location, and pay parameters separately
        if (search) {
            params.append('search', search);
        }
        if (location) {
            params.append('location', location);
        }
        if (pay) {
            params.append('pay', pay);
        }
        
        const apiUrl = `/api/jobs?${params}`;
        console.log('Fetching jobs from:', apiUrl);
        
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('API error:', response.status, errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received data:', { jobsCount: data.jobs?.length, total: data.total });
        
        if (!data || !data.jobs) {
            throw new Error('Invalid response from server');
        }
        
        if (data.jobs.length === 0) {
            container.innerHTML = '<div class="loading">No jobs found. Add data sources to start collecting jobs.</div>';
            return;
        }
        
        try {
            const jobCards = data.jobs.map(job => {
                try {
                    return createJobCard(job);
                } catch (cardError) {
                    console.error('Error creating card for job:', job.id, cardError);
                    return ''; // Skip this job card if there's an error
                }
            }).filter(card => card !== '').join('');
            
            if (jobCards) {
                container.innerHTML = jobCards;
            } else {
                container.innerHTML = '<div class="loading">Error displaying jobs. Please refresh the page.</div>';
                return;
            }
        } catch (error) {
            console.error('Error creating job cards:', error);
            container.innerHTML = '<div class="loading">Error displaying jobs. Please refresh the page.</div>';
            return;
        }
        
        // If Details button is active, show descriptions for new jobs
        const detailsButton = document.querySelector('.filter-btn[data-filter="details"]');
        if (detailsButton && detailsButton.getAttribute('data-expanded') === 'true') {
            const allDescriptions = document.querySelectorAll('.job-description');
            allDescriptions.forEach(desc => {
                desc.style.display = 'block';
                desc.classList.add('description-expanded');
            });
        }
        
        // Update pagination info
        const totalPages = Math.ceil(data.total / perPage);
        const pageInfo = document.getElementById('page-info');
        if (pageInfo) {
            pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        }
        
        // Update pagination button states
        document.getElementById('prev-page').disabled = currentPage === 1;
        document.getElementById('next-page').disabled = currentPage >= totalPages;
    } catch (error) {
        console.error('Failed to load jobs:', error);
        container.innerHTML = `<div class="loading">Failed to load jobs: ${error.message}. Please refresh the page.</div>`;
    }
}

// Create job card with new design
function createJobCard(job) {
    const companyName = job.company || 'Unknown Company';
    const companyInitials = getCompanyInitials(companyName);
    const location = job.location || 'Location not specified';
    const level = job.level || 'individual';
    
    // Determine work model (default to Hybrid if not specified)
    const workModel = detectWorkModel(job.description || '', location);
    
    // Generate salary estimate (if not available)
    const salary = estimateSalary(level, job.title || '');
    
    // Calculate time ago
    const timeAgo = getTimeAgo(job.posted_date || job.collected_date);
    
    // Determine category
    const category = detectCategory(job.title || '', job.description || '');
    
    return `
        <div class="job-card">
            <div class="job-header">
                <div class="job-title-section">
                    <div class="job-title">${escapeHtml(job.title || 'Untitled Position')}</div>
                    <div class="job-company-row">
                        <div class="company-icon">${companyInitials}</div>
                        <div class="job-company">${escapeHtml(companyName)}</div>
                    </div>
                </div>
            </div>
            <div class="job-meta-row">
                ${category ? `<span class="job-category">${category}</span>` : ''}
                <span class="job-location">${escapeHtml(location)}</span>
                <span class="job-model">${workModel}</span>
                ${salary ? `<span class="job-salary">${salary}</span>` : ''}
            </div>
            ${job.description ? `
                <div class="job-description-container" data-job-id="${job.id}">
                    <div class="job-description" style="display: none;">${escapeHtml(job.description)}</div>
                </div>
            ` : ''}
            <div class="job-actions">
                <span class="job-time">${timeAgo}</span>
                <a href="${job.url || '#'}" target="_blank" class="btn-apply">Apply</a>
            </div>
        </div>
    `;
}

// Get company initials for icon
function getCompanyInitials(companyName) {
    if (!companyName) return '?';
    const words = companyName.trim().split(/\s+/);
    if (words.length >= 2) {
        return (words[0][0] + words[1][0]).toUpperCase();
    }
    return companyName.substring(0, 2).toUpperCase();
}

// Detect work model from description
function detectWorkModel(description, location) {
    const desc = (description + ' ' + location).toLowerCase();
    if (desc.includes('remote') || desc.includes('work from home')) {
        return 'Remote';
    } else if (desc.includes('hybrid')) {
        return 'Hybrid';
    } else if (desc.includes('onsite') || desc.includes('on-site')) {
        return 'Onsite';
    }
    return 'Hybrid'; // Default
}

// Estimate salary based on level
function estimateSalary(level, title) {
    const titleLower = title.toLowerCase();
    const isSenior = level === 'senior' || titleLower.includes('senior') || titleLower.includes('sr');
    const isExecutive = level === 'executive' || titleLower.includes('director') || titleLower.includes('vp') || titleLower.includes('executive');
    
    if (isExecutive) {
        return '$200,000 - $350,000';
    } else if (isSenior) {
        return '$120,000 - $200,000';
    } else {
        return '$80,000 - $150,000';
    }
}

// Detect category from title and description
function detectCategory(title, description) {
    const text = (title + ' ' + description).toLowerCase();
    
    if (text.includes('data') || text.includes('analytics')) return 'Data';
    if (text.includes('engineer') || text.includes('developer')) return 'Engineering';
    if (text.includes('product')) return 'Product';
    if (text.includes('sales') || text.includes('business development')) return 'Sales';
    if (text.includes('marketing')) return 'Marketing';
    if (text.includes('operations')) return 'Operations';
    if (text.includes('design') || text.includes('ux') || text.includes('ui')) return 'Design';
    if (text.includes('field service') || text.includes('service')) return 'Field Service';
    
    return 'Other';
}

// Get time ago string
function getTimeAgo(dateString) {
    if (!dateString) return 'Just now';
    
    try {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        if (diffDays < 7) return `${diffDays}d`;
        return date.toLocaleDateString();
    } catch (e) {
        return 'Recently';
    }
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Refresh now
async function refreshNow() {
    const btn = document.getElementById('refresh-btn');
    if (!btn) return;
    
    btn.disabled = true;
    btn.textContent = 'Refreshing...';
    
    try {
        const response = await fetch('/api/refresh-now', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert('Refresh successful!');
            loadRefreshStatus();
            loadJobs();
        } else {
            alert('Refresh failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Refresh failed: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Refresh Now';
    }
}

// Add data source
async function addSource(e) {
    e.preventDefault();
    
    const type = document.getElementById('source-type').value;
    let url = document.getElementById('source-url').value.trim();
    const name = document.getElementById('source-name').value.trim();
    
    // For API type, allow empty URL (will be converted to 'all' by backend)
    if (type === 'api' && !url) {
        url = 'all';
    }
    
    try {
        const response = await fetch('/api/sources', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ type, url, name })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('Source added successfully!');
            document.getElementById('add-source-form').reset();
            // Reset source type to api
            document.getElementById('source-type').value = 'api';
            updateSourceFormLabels();
            // Reload sources list
            await loadSources();
            loadRefreshStatus();
            loadJobs();
        } else {
            alert('Failed to add: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to add: ' + error.message);
    }
}

// Update form labels based on source type
function updateSourceFormLabels() {
    const sourceType = document.getElementById('source-type').value;
    const urlLabel = document.getElementById('source-url-label');
    const urlInput = document.getElementById('source-url');
    const urlHint = document.getElementById('source-url-hint');
    
    if (sourceType === 'api') {
        urlLabel.textContent = 'Search Query:';
        urlInput.placeholder = 'e.g., field service, software engineer, or leave empty for all jobs';
        urlHint.textContent = 'For Adzuna API: Enter keywords to search, or leave empty to fetch all jobs.';
    } else if (sourceType === 'rss') {
        urlLabel.textContent = 'RSS Feed URL:';
        urlInput.placeholder = 'https://example.com/jobs.rss';
        urlHint.textContent = 'Enter the full URL of the RSS feed.';
    } else if (sourceType === 'url') {
        urlLabel.textContent = 'Company URL:';
        urlInput.placeholder = 'https://company.com/careers';
        urlHint.textContent = 'Enter the full URL of the company careers page.';
    }
}

// Add event listener for source type change
document.addEventListener('DOMContentLoaded', function() {
    const sourceTypeSelect = document.getElementById('source-type');
    if (sourceTypeSelect) {
        sourceTypeSelect.addEventListener('change', updateSourceFormLabels);
        updateSourceFormLabels(); // Initialize labels
    }
});

// Load data sources list
async function loadSources() {
    try {
        const response = await fetch('/api/sources');
        if (!response.ok) {
            console.error('Failed to fetch sources:', response.status);
            return;
        }
        const data = await response.json();
        console.log('Data sources:', data.sources);
        
        // Display sources in admin panel
        const container = document.getElementById('sources-container');
        if (!container) {
            console.error('sources-container element not found');
            return;
        }
        
        if (container) {
            if (data.sources.length === 0) {
                container.innerHTML = '<p style="color: #999;">No data sources added yet.</p>';
            } else {
                container.innerHTML = data.sources.map(source => {
                    const displayName = source.name || 'Unnamed';
                    const displayUrl = source.url || '';
                    const displayType = source.type || 'unknown';
                    const sourceId = source.id || 0;
                    return `
                    <div style="padding: 10px; margin-bottom: 8px; background: white; border: 1px solid #e5e5e5; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${escapeHtml(displayName)}</strong>
                            <div style="font-size: 0.85em; color: #999; margin-top: 4px;">
                                URL: ${escapeHtml(displayUrl.length > 60 ? displayUrl.substring(0, 60) + '...' : displayUrl)} | Type: ${displayType}
                            </div>
                        </div>
                        <button onclick="deleteSource(${sourceId})" style="padding: 6px 12px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85em;">Delete</button>
                    </div>
                `;
                }).join('');
            }
        }
    } catch (error) {
        console.error('Failed to load sources:', error);
    }
}

// Delete data source
async function deleteSource(sourceId) {
    if (!confirm('Are you sure you want to delete this data source?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/sources/${sourceId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            alert('Data source deleted successfully!');
            loadSources();
            loadRefreshStatus();
        } else {
            alert('Failed to delete: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to delete: ' + error.message);
    }
}

// Toggle all job descriptions visibility
function toggleAllJobDescriptions(button) {
    const allDescriptions = document.querySelectorAll('.job-description');
    const isExpanded = button.getAttribute('data-expanded') === 'true';
    
    if (isExpanded) {
        // Collapse - hide all descriptions
        allDescriptions.forEach(desc => {
            desc.style.display = 'none';
            desc.classList.remove('description-expanded');
        });
        button.setAttribute('data-expanded', 'false');
        button.classList.remove('active');
    } else {
        // Expand - show first 3 lines for all descriptions
        allDescriptions.forEach(desc => {
            desc.style.display = 'block';
            desc.classList.add('description-expanded');
        });
        button.setAttribute('data-expanded', 'true');
        button.classList.add('active');
    }
}
