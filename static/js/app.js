// AI + Biology Events (Seminars, Workshops, etc.) in the Greater Boston Area - Frontend JavaScript

class EventsApp {
    constructor() {
        this.events = [];
        this.filteredEvents = [];
        this.currentFilters = {
            search: '',
            cs: false,
            biology: false,
            mit: true,
            harvard: true,
            bu: true,
            brown: true,
            others: true
        };
        this.eventListenersSetup = false;
        
        console.log('EventsApp constructor called');
        this.init().catch(error => {
            console.error('Error initializing EventsApp:', error);
        });
    }
    
    async init() {
        console.log('EventsApp init started');
        this.bindEvents();
        await this.loadEvents();
        this.setupAutoRefresh();
        
        // Initialize calendar properties
        this.calendarView = 'month';
        this.currentDate = new Date();
        console.log('Calendar initialized with date:', this.currentDate.toLocaleDateString());
        
        // Test if updateCalendar method exists
        console.log('updateCalendar method exists:', typeof this.updateCalendar);
        console.log('Available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(this)));
        
        console.log('EventsApp init completed');
    }
    
    bindEvents() {
        // Search input
        document.getElementById('searchInput').addEventListener('input', async (e) => {
            this.currentFilters.search = e.target.value.toLowerCase();
            await this.applyFilters();
        });
        
        // Category filters
        document.getElementById('csFilter').addEventListener('change', async (e) => {
            this.currentFilters.cs = e.target.checked;
            await this.applyFilters();
        });
        
        document.getElementById('biologyFilter').addEventListener('change', async (e) => {
            this.currentFilters.biology = e.target.checked;
            await this.applyFilters();
        });
        
        // Institution filters
        document.getElementById('mitFilter').addEventListener('change', async (e) => {
            this.currentFilters.mit = e.target.checked;
            await this.applyFilters();
        });
        
        document.getElementById('harvardFilter').addEventListener('change', async (e) => {
            this.currentFilters.harvard = e.target.checked;
            await this.applyFilters();
        });
        
        document.getElementById('buFilter').addEventListener('change', async (e) => {
            this.currentFilters.bu = e.target.checked;
            await this.applyFilters();
        });
        
        document.getElementById('brownFilter').addEventListener('change', async (e) => {
            this.currentFilters.brown = e.target.checked;
            await this.applyFilters();
        });
        
        document.getElementById('othersFilter').addEventListener('change', async (e) => {
            this.currentFilters.others = e.target.checked;
            await this.applyFilters();
        });
        
        // Buttons
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshEvents();
        });
        
        document.getElementById('statsBtn').addEventListener('click', () => {
            this.showStats();
        });
    }
    
    async loadEvents() {
        try {
            const params = new URLSearchParams({
                search: this.currentFilters.search,
                cs: this.currentFilters.cs.toString(),
                biology: this.currentFilters.biology.toString(),
                mit: this.currentFilters.mit.toString(),
                harvard: this.currentFilters.harvard.toString(),
                bu: this.currentFilters.bu.toString(),
                brown: this.currentFilters.brown.toString(),
                others: this.currentFilters.others.toString()
            });
            
            const response = await fetch(`/api/events?${params}`);
            const data = await response.json();
            
            if (data.success) {
                this.events = data.events;
                this.filteredEvents = [...this.events];
                console.log('Loaded', this.events.length, 'events');
                this.renderEvents();
                this.updateEventCount();
                
                // Update calendar after events are loaded
                console.log('About to call updateCalendar() after loading events...');
                console.log('this.updateCalendar exists:', typeof this.updateCalendar);
                try {
                    this.updateCalendar();
                    console.log('updateCalendar() called successfully after loading events');
                } catch (error) {
                    console.error('Error calling updateCalendar() after loading events:', error);
                }
            } else {
                this.showError('Failed to load events: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }
    
    async applyFilters() {
        // Reload events with current filters from the server
        await this.loadEvents();
    }
    
    renderEvents() {
        const eventsList = document.getElementById('eventsList');
        
        if (this.filteredEvents.length === 0) {
            eventsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-calendar-times"></i>
                    <h5>No events found</h5>
                    <p>Try adjusting your filters or refresh the events.</p>
                </div>
            `;
            return;
        }
        
        eventsList.innerHTML = this.filteredEvents.map(event => this.renderEventItem(event)).join('');
        
        // Add click handlers to event items
        eventsList.querySelectorAll('.event-item').forEach((item, index) => {
            item.addEventListener('click', () => {
                this.showEventDetails(this.filteredEvents[index]);
            });
        });
        
        // Update the calendar
        console.log('About to update calendar...');
        this.updateCalendar();
    }
    
    renderEventItem(event) {
        let date = this.parseISODateLocal(event.date);
        if (!this.isValidDate(date)) {
            date = new Date();
        }
        const formattedDate = date.toLocaleDateString('en-US', { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric' 
        });
        
        const timeStr = (event.time || '').trim();
        const showTime = timeStr && timeStr.toLowerCase() !== '12:00 am' && timeStr !== '00:00';
        const time = showTime ? ` • ${timeStr}` : '';
        const location = event.location ? ` • ${event.location}` : '';
        
        const badges = [];
        
        // Event type badge
        if (event.is_virtual) {
            badges.push('<span class="event-badge badge-virtual"><i class="fas fa-video me-1"></i>Virtual</span>');
        } else {
            badges.push('<span class="event-badge badge-onsite"><i class="fas fa-map-marker-alt me-1"></i>On-site</span>');
        }
        
        // Registration badge
        if (event.requires_registration) {
            badges.push('<span class="event-badge badge-registration"><i class="fas fa-user-plus me-1"></i>Registration Required</span>');
        }
        
        // Category badges
        event.categories.forEach(category => {
            const icon = category === 'computer science' ? 'fas fa-laptop-code' : 'fas fa-dna';
            const cssClass = category === 'computer science' ? 'cs' : 'biology';
            badges.push(`<span class="event-badge badge-category ${cssClass}"><i class="${icon} me-1"></i>${category}</span>`);
        });
        
        return `
            <div class="list-group-item event-item" data-event-id="${event.id}">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="event-date">
                            <i class="fas fa-calendar-day me-1"></i>${formattedDate}${time}${location}
                        </div>
                        <div class="event-title">${this.highlightSearch(event.title)}</div>
                        <div class="event-description">${this.highlightSearch(event.description)}</div>
                        <div class="event-meta">
                            ${badges.join('')}
                            <div class="mt-2">
                                <small class="text-muted">
                                    <i class="fas fa-globe me-1"></i>${new URL(event.source_url).hostname}
                                </small>
                            </div>
                        </div>
                    </div>
                    <div class="ms-2">
                        <i class="fas fa-chevron-right text-muted"></i>
                    </div>
                </div>
            </div>
        `;
    }
    
    highlightSearch(text) {
        if (!this.currentFilters.search || !text) return text;
        
        const regex = new RegExp(`(${this.currentFilters.search})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    }
    
    updateEventCount() {
        const countElement = document.getElementById('eventCount');
        countElement.textContent = this.filteredEvents.length;
    }
    
    showEventDetails(event) {
        const modal = new bootstrap.Modal(document.getElementById('eventModal'));
        
        document.getElementById('eventModalTitle').textContent = event.title;
        document.getElementById('eventModalLink').href = event.url;
        
        let date = this.parseISODateLocal(event.date);
        if (!this.isValidDate(date)) {
            date = new Date();
        }
        const formattedDate = date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        const categories = event.categories.length > 0 
            ? event.categories.map(cat => `<span class="badge bg-primary me-1">${cat}</span>`).join('')
            : '<span class="text-muted">No categories assigned</span>';
        
        document.getElementById('eventModalBody').innerHTML = `
            <div class="event-detail-row">
                <div class="event-detail-label">Date & Time</div>
                <div class="event-detail-value">
                    <i class="fas fa-calendar-day me-1"></i>${formattedDate}
                    ${event.time ? `<br><i class="fas fa-clock me-1"></i>${event.time}` : ''}
                </div>
            </div>
            
            ${event.location ? `
            <div class="event-detail-row">
                <div class="event-detail-label">Location</div>
                <div class="event-detail-value">
                    <i class="fas fa-map-marker-alt me-1"></i>${event.location}
                </div>
            </div>
            ` : ''}
            
            <div class="event-detail-row">
                <div class="event-detail-label">Event Type</div>
                <div class="event-detail-value">
                    ${event.is_virtual ? 
                        '<span class="badge bg-info"><i class="fas fa-video me-1"></i>Virtual Event</span>' : 
                        '<span class="badge bg-secondary"><i class="fas fa-map-marker-alt me-1"></i>On-site Event</span>'
                    }
                    ${event.requires_registration ? 
                        '<span class="badge bg-warning ms-1"><i class="fas fa-user-plus me-1"></i>Registration Required</span>' : 
                        '<span class="badge bg-success ms-1"><i class="fas fa-check me-1"></i>No Registration Required</span>'
                    }
                </div>
            </div>
            
            <div class="event-detail-row">
                <div class="event-detail-label">Categories</div>
                <div class="event-detail-value">${categories}</div>
            </div>
            
            ${event.description ? `
            <div class="event-detail-row">
                <div class="event-detail-label">Description</div>
                <div class="event-detail-value">${event.description}</div>
            </div>
            ` : ''}
            
            <div class="event-detail-row">
                <div class="event-detail-label">Event URL</div>
                <div class="event-detail-value">
                    <a href="${event.url}" target="_blank" class="text-decoration-none">
                        <i class="fas fa-external-link-alt me-1"></i>View Event Details
                    </a>
                </div>
            </div>
            
            <div class="event-detail-row">
                <div class="event-detail-label">Source Website</div>
                <div class="event-detail-value">
                    <a href="${event.source_url}" target="_blank" class="text-decoration-none">
                        <i class="fas fa-globe me-1"></i>${new URL(event.source_url).hostname}
                    </a>
                </div>
            </div>
        `;
        
        modal.show();
    }
    
    async refreshEvents() {
        try {
            const response = await fetch('/api/scrape', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`Successfully refreshed events! Found ${data.new_events} new events.`);
                await this.loadEvents();
            } else {
                this.showError('Failed to refresh events: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }
    
    async showStats() {
        try {
            const response = await fetch('/api/stats');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                
                document.getElementById('statsContent').innerHTML = `
                    <div class="row">
                        <div class="col-md-4">
                            <div class="stats-card text-center">
                                <div class="stats-number">${stats.total_events}</div>
                                <div class="stats-label">Total Events</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="stats-card text-center">
                                <div class="stats-number">${stats.today_events}</div>
                                <div class="stats-label">Today</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="stats-card text-center">
                                <div class="stats-number">${stats.week_events}</div>
                                <div class="stats-label">This Week</div>
                            </div>
                        </div>
                    </div>
                    
                    <h6 class="mt-4 mb-3">Recent Scraping Activity</h6>
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Source</th>
                                    <th>Status</th>
                                    <th>Events Found</th>
                                    <th>Last Updated</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${stats.recent_scrapes.map(scrape => `
                                    <tr>
                                        <td>${new URL(scrape[0]).hostname}</td>
                                        <td>
                                            <span class="badge ${scrape[1] === 'success' ? 'bg-success' : 'bg-danger'}">
                                                ${scrape[1]}
                                            </span>
                                        </td>
                                        <td>${scrape[2]}</td>
                                        <td>${new Date(scrape[3]).toLocaleString()}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
                
                const modal = new bootstrap.Modal(document.getElementById('statsModal'));
                modal.show();
            } else {
                this.showError('Failed to load stats: ' + data.error);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }
    

    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showError(message) {
        this.showNotification(message, 'danger');
    }
    
    showNotification(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    setupAutoRefresh() {
        // Refresh events every 30 minutes
        setInterval(() => {
            this.loadEvents();
        }, 30 * 60 * 1000);
        
        // Setup Google Calendar integration
        this.setupGoogleCalendar();
    }
    
    setupGoogleCalendar() {
        // Update Google Calendar iframe with current events
        const updateGoogleCalendar = () => {
            const calendarIframe = document.getElementById('googleCalendar');
            if (calendarIframe && this.filteredEvents.length > 0) {
                // Create a simple calendar view with event links
                // For now, we'll add a note about events
                const eventCount = this.filteredEvents.length;
                console.log(`Google Calendar updated with ${eventCount} events`);
            }
        };
        
        // Update Google Calendar when events change
        this.updateGoogleCalendar = updateGoogleCalendar;
    }
    
    updateEventTimeline() {
        this.updateCalendar();
    }
    
    updateCalendar() {
        console.log('=== updateCalendar() called ===');
        console.log('this object:', this);
        console.log('this.calendarView:', this.calendarView);
        console.log('this.currentDate:', this.currentDate);
        
        const calendarContainer = document.getElementById('calendarContainer');
        if (!calendarContainer) {
            console.log('Calendar container not found');
            return;
        }
        
        // Initialize calendar if not already done
        if (!this.calendarView || !this.currentDate) {
            console.log('Initializing calendar...');
            this.calendarView = 'month';
            this.currentDate = new Date();
        }
        
        console.log('Updating calendar with', this.filteredEvents.length, 'events');
        console.log('Current date:', this.currentDate.toLocaleDateString());
        console.log('Calendar view:', this.calendarView);
        
        try {
            console.log('Calendar view is:', this.calendarView);
            if (this.calendarView === 'month') {
                console.log('Rendering month view...');
                this.renderMonthView();
            } else if (this.calendarView === 'week') {
                console.log('Rendering week view...');
                this.renderWeekTimeGridView();
            } else if (this.calendarView === 'day') {
                console.log('Rendering day view...');
                this.renderDayView();
            }
            console.log('=== updateCalendar() completed ===');
        } catch (error) {
            console.error('Error rendering calendar:', error);
            calendarContainer.innerHTML = `
                <div class="calendar-empty">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h6>Calendar Error</h6>
                    <p>Error loading calendar view</p>
                </div>
            `;
        }
    }
    
    renderMonthView() {
        console.log('Rendering month view...');
        const calendarContainer = document.getElementById('calendarContainer');
        if (!calendarContainer) {
            console.error('Calendar container not found!');
            return;
        }
        
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());
        
        const monthName = this.currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        console.log('Month name:', monthName);
        
        const calendarHTML = `
            <div class="calendar-header">
                <div class="calendar-nav">
                    <button class="calendar-nav-btn" data-action="previous">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="calendar-title">${monthName}</span>
                    <button class="calendar-nav-btn" data-action="next">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
            <div class="calendar-grid">
                <div class="calendar-weekdays">
                    <div class="calendar-weekday">Sun</div>
                    <div class="calendar-weekday">Mon</div>
                    <div class="calendar-weekday">Tue</div>
                    <div class="calendar-weekday">Wed</div>
                    <div class="calendar-weekday">Thu</div>
                    <div class="calendar-weekday">Fri</div>
                    <div class="calendar-weekday">Sat</div>
                </div>
                <div class="calendar-days">
                    ${this.generateMonthDays(startDate, lastDay)}
                </div>
            </div>
        `;
        
        calendarContainer.innerHTML = calendarHTML;
        
        // Add event listeners for calendar navigation
        this.setupCalendarEventListeners();
    }
    
    generateMonthDays(startDate, lastDay) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        let daysHTML = '';
        let currentDate = new Date(startDate);
        
        // Generate 6 weeks of days (42 days)
        for (let i = 0; i < 42; i++) {
            const isCurrentMonth = currentDate.getMonth() === this.currentDate.getMonth();
            const isToday = currentDate.getTime() === today.getTime();
            const dayEvents = this.getEventsForDate(currentDate);
            
            let dayClass = 'calendar-day';
            if (!isCurrentMonth) dayClass += ' other-month';
            if (isToday) dayClass += ' today';
            if (dayEvents.length > 0) dayClass += ' has-events';
            
            const eventsHTML = dayEvents.map(event => {
                const categories = event.categories || [];
                const isCS = categories.some(cat => cat.toLowerCase().includes('computer science'));
                const isBiology = categories.some(cat => cat.toLowerCase().includes('biology'));
                
                let eventClass = 'calendar-event';
                if (isCS && isBiology) {
                    eventClass += ' cs-event biology-event';
                } else if (isCS) {
                    eventClass += ' cs-event';
                } else if (isBiology) {
                    eventClass += ' biology-event';
                }
                
                if (event.is_virtual) {
                    eventClass += ' virtual';
                } else {
                    eventClass += ' onsite';
                }
                
                return `
                    <div class="${eventClass}" 
                         title="${event.title}"
                         data-event-id="${event.id}"
                         data-event='${JSON.stringify(event).replace(/'/g, "&apos;")}'>
                        ${event.title.substring(0, 15)}${event.title.length > 15 ? '...' : ''}
                    </div>
                `;
            }).join('');
            
            const isoDate = new Date(currentDate).toISOString().split('T')[0];
            daysHTML += `
                <div class="${dayClass}" data-date="${isoDate}">
                    <div class="calendar-day-number">${currentDate.getDate()}</div>
                    <div class="calendar-events">${eventsHTML}</div>
                </div>
            `;
            
            currentDate.setDate(currentDate.getDate() + 1);
        }
        
        return daysHTML;
    }
    
    renderWeekView() {
        // Kept for backward compatibility if referenced elsewhere
        this.renderWeekTimeGridView();
    }
    
    renderWeekTimeGridView() {
        console.log('Rendering week time-grid view...');
        const calendarContainer = document.getElementById('calendarContainer');
        if (!calendarContainer) return;
        const weekStart = this.getWeekStart(this.currentDate);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);
        const weekRange = `${weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;

        const hours = Array.from({ length: 24 }, (_, h) => h);
        const dayHeaders = Array.from({ length: 7 }, (_, i) => {
            const d = new Date(weekStart);
            d.setDate(d.getDate() + i);
            const iso = d.toISOString().split('T')[0];
            const label = `${d.toLocaleDateString('en-US', { weekday: 'short' })} ${d.getDate()}`;
            return `<div class="calendar-week-day-header" data-date="${iso}">${label}</div>`;
        }).join('');

        const gridHTML = `
            <div class="calendar-header">
                <div class="calendar-nav">
                    <button class="calendar-nav-btn" data-action="previous"><i class="fas fa-chevron-left"></i></button>
                    <span class="calendar-title">${weekRange}</span>
                    <button class="calendar-nav-btn" data-action="next"><i class="fas fa-chevron-right"></i></button>
                </div>
            </div>
            <div class="time-grid">
                <div class="time-grid-sidebar">
                    ${hours.map(h => `<div class="time-grid-hour">${(h % 12) === 0 ? 12 : (h % 12)} ${h < 12 ? 'AM' : 'PM'}</div>`).join('')}
                </div>
                <div class="time-grid-content">
                    <div class="time-grid-day-headers">${dayHeaders}</div>
                    <div class="time-grid-rows">
                        ${hours.map(() => `<div class="time-grid-row"></div>`).join('')}
                        <div class="time-grid-events">
                            ${this.generateWeekEventsPositioned(weekStart)}
                        </div>
                    </div>
                </div>
            </div>
        `;
        calendarContainer.innerHTML = gridHTML;
        this.setupCalendarEventListeners();
    }

    renderDayView() {
        console.log('Rendering day view...');
        const calendarContainer = document.getElementById('calendarContainer');
        if (!calendarContainer) return;
        const d = new Date(this.currentDate);
        d.setHours(0,0,0,0);
        const title = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
        const hours = Array.from({ length: 24 }, (_, h) => h);
        const gridHTML = `
            <div class="calendar-header">
                <div class="calendar-nav">
                    <button class="calendar-nav-btn" data-action="previous"><i class="fas fa-chevron-left"></i></button>
                    <span class="calendar-title">${title}</span>
                    <button class="calendar-nav-btn" data-action="next"><i class="fas fa-chevron-right"></i></button>
                </div>
            </div>
            <div class="time-grid">
                <div class="time-grid-sidebar">
                    ${hours.map(h => `<div class="time-grid-hour">${(h % 12) === 0 ? 12 : (h % 12)} ${h < 12 ? 'AM' : 'PM'}</div>`).join('')}
                </div>
                <div class="time-grid-content single-day">
                    <div class="time-grid-day-headers"><div class="calendar-week-day-header">${d.toLocaleDateString('en-US', { weekday: 'short' })} ${d.getDate()}</div></div>
                    <div class="time-grid-rows">
                        ${hours.map(() => `<div class="time-grid-row"></div>`).join('')}
                        <div class="time-grid-events">
                            ${this.generateDayEventsPositioned(d)}
                        </div>
                    </div>
                </div>
            </div>
        `;
        calendarContainer.innerHTML = gridHTML;
        this.setupCalendarEventListeners();
    }

    // Helpers to place events on time grid
    parseEventTimeToMinutes(event) {
        // Robust parsing for many human formats; fallback to 9:00 AM if unknown
        let raw = (event.time || '').trim();
        if (!raw) return 9 * 60;

        // Normalize common variants
        raw = raw.replace(/\u2013|\u2014|–|—/g, '-'); // en/em dashes to hyphen
        raw = raw.replace(/\.(?=\s|$)/g, ''); // remove dots in a.m./p.m.
        raw = raw.replace(/\((?:[^()]*?)\)/g, ' '); // remove parenthetical notes (e.g., (ET))
        raw = raw.replace(/\b(ET|EST|EDT|eastern time|eastern|boston time)\b/gi, ' '); // drop TZ words
        raw = raw.replace(/\s+/g, ' ').trim();

        // If it's a range like "1 pm - 2 pm", take the first part
        if (raw.includes('-')) {
            raw = raw.split('-')[0].trim();
        }

        const lower = raw.toLowerCase();

        // Keywords
        if (lower.includes('noon')) return 12 * 60;
        if (lower.includes('midnight')) return 0;

        // Patterns
        // 1) 12-hour with am/pm attached or spaced: "1pm", "1 pm", "1:30 PM"
        let m = lower.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$/i);
        if (!m) {
            // also allow attached without space
            m = lower.match(/^(\d{1,2})(?::(\d{2}))?(am|pm)$/i);
        }
        if (m) {
            let hour = parseInt(m[1], 10);
            const minute = parseInt(m[2] || '0', 10);
            const ampm = (m[3] || '').toUpperCase();
            if (hour === 12) hour = 0;
            if (ampm === 'PM') hour += 12;
            return hour * 60 + minute;
        }

        // 2) 24-hour like "13:00"
        const t24 = lower.match(/^(\d{1,2})(?::(\d{2}))$/);
        if (t24) {
            const hour = parseInt(t24[1], 10);
            const minute = parseInt(t24[2] || '0', 10);
            return hour * 60 + minute;
        }

        // 3) Ambiguous "1" or "1:30" without am/pm. Heuristic: treat 1-6 as PM, 7-11 as AM
        const amb = lower.match(/^(\d{1,2})(?::(\d{2}))?$/);
        if (amb) {
            let hour = parseInt(amb[1], 10);
            const minute = parseInt(amb[2] || '0', 10);
            if (hour >= 1 && hour <= 6) hour += 12; // assume afternoon
            // 7-11 -> morning, 12 stays 12
            return hour * 60 + minute;
        }

        return 9 * 60;
    }

    // Compute positioned blocks for a single day's events with overlap columns
    layoutDayEvents(events) {
        const DEFAULT_DURATION_MIN = 60;
        const items = events.map(ev => {
            const start = this.parseEventTimeToMinutes(ev);
            const end = start + DEFAULT_DURATION_MIN;
            return { ev, start, end, col: 0 };
        }).sort((a, b) => a.start - b.start || a.end - b.end);

        // Build overlap groups
        const groups = [];
        let current = [];
        let groupEnd = -1;
        for (const it of items) {
            if (current.length === 0 || it.start < groupEnd) {
                current.push(it);
                groupEnd = Math.max(groupEnd, it.end);
            } else {
                groups.push(current);
                current = [it];
                groupEnd = it.end;
            }
        }
        if (current.length) groups.push(current);

        const totalMinutes = 24 * 60;
        const positioned = [];

        groups.forEach(group => {
            const active = [];
            const freeCols = [];
            let maxCols = 0;
            group.forEach(item => {
                for (let i = active.length - 1; i >= 0; i--) {
                    if (active[i].end <= item.start) {
                        freeCols.push(active[i].col);
                        active.splice(i, 1);
                    }
                }
                if (freeCols.length) {
                    freeCols.sort((a, b) => a - b);
                    item.col = freeCols.shift();
                } else {
                    item.col = active.length;
                }
                active.push(item);
                maxCols = Math.max(maxCols, active.length, item.col + 1);
            });

            group.forEach(item => {
                const topPct = (item.start / totalMinutes) * 100;
                const heightPct = ((item.end - item.start) / totalMinutes) * 100;
                const widthPct = 100 / maxCols;
                const leftPct = item.col * widthPct;
                positioned.push({ ev: item.ev, topPct, heightPct, leftPct, widthPct });
            });
        });

        return positioned;
    }

    generateWeekEventsPositioned(weekStart) {
        const dayColumns = Array.from({ length: 7 }, () => []);
        for (let i = 0; i < 7; i++) {
            const d = new Date(weekStart);
            d.setDate(d.getDate() + i);
            const events = this.getEventsForDate(d);
            dayColumns[i] = events;
        }
        const eventBlocks = [];
        dayColumns.forEach((events, dayIndex) => {
            const laidOut = this.layoutDayEvents(events);
            laidOut.forEach(p => {
                const categories = p.ev.categories || [];
                const isCS = categories.some(cat => cat.toLowerCase().includes('computer science'));
                const isBiology = categories.some(cat => cat.toLowerCase().includes('biology'));
                let cls = 'time-event';
                if (isCS) cls += ' cs-event';
                if (isBiology) cls += ' biology-event';
                if (p.ev.is_virtual) cls += ' virtual'; else cls += ' onsite';
                const dayLeftPct = (dayIndex / 7) * 100;
                const dayWidthPct = 100 / 7;
                const left = dayLeftPct + (p.leftPct * dayWidthPct / 100);
                const width = (p.widthPct * dayWidthPct) / 100;
                eventBlocks.push(`
                    <div class="${cls}" style="top:${p.topPct}%; left:${left}%; height:${p.heightPct}%; width:${width}%" data-event='${JSON.stringify(p.ev).replace(/'/g, "&apos;")}' title='${p.ev.title}'>
                        <div class="time-event-title">${p.ev.title}</div>
                        ${p.ev.time ? `<div class=\"time-event-time\">${p.ev.time}</div>` : ''}
                    </div>
                `);
            });
        });
        return eventBlocks.join('');
    }

    generateDayEventsPositioned(date) {
        const events = this.getEventsForDate(date);
        const laidOut = this.layoutDayEvents(events);
        return laidOut.map(p => {
            const categories = p.ev.categories || [];
            const isCS = categories.some(cat => cat.toLowerCase().includes('computer science'));
            const isBiology = categories.some(cat => cat.toLowerCase().includes('biology'));
            let cls = 'time-event';
            if (isCS) cls += ' cs-event';
            if (isBiology) cls += ' biology-event';
            if (p.ev.is_virtual) cls += ' virtual'; else cls += ' onsite';
            return `
                <div class="${cls}" style="top:${p.topPct}%; left:${p.leftPct}%; height:${p.heightPct}%; width:${p.widthPct}%" data-event='${JSON.stringify(p.ev).replace(/'/g, "&apos;")}' title='${p.ev.title}'>
                    <div class="time-event-title">${p.ev.title}</div>
                    ${p.ev.time ? `<div class=\"time-event-time\">${p.ev.time}</div>` : ''}
                </div>
            `;
        }).join('');
    }
    
    getEventsForDate(date) {
        const targetStr = this.formatLocalDateYYYYMMDD(date);
        const events = this.filteredEvents.filter(event => {
            const eventDate = this.parseISODateLocal(event.date);
            if (!this.isValidDate(eventDate)) return false;
            const eventDateStr = this.formatLocalDateYYYYMMDD(eventDate);
            return eventDateStr === targetStr;
        });
        
        if (events.length > 0) {
            console.log(`Found ${events.length} events for ${targetStr}:`, events.map(e => e.title.substring(0, 30)));
        }
        
        return events;
    }
    
    getWeekStart(date) {
        const d = new Date(date);
        const day = d.getDay();
        const diff = d.getDate() - day;
        return new Date(d.setDate(diff));
    }

    // --- Date helpers to avoid UTC off-by-one issues ---
    formatLocalDateYYYYMMDD(date) {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
    }

    parseISODateLocal(iso) {
        // Expect 'YYYY-MM-DD'; create Date in local time at midnight
        if (!iso || typeof iso !== 'string') return new Date(iso);
        const m = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (!m) return new Date(iso);
        const y = parseInt(m[1], 10);
        const mo = parseInt(m[2], 10) - 1;
        const d = parseInt(m[3], 10);
        return new Date(y, mo, d, 0, 0, 0, 0);
    }

    isValidDate(d) {
        return d instanceof Date && !isNaN(d.getTime());
    }
    
    changeCalendarView(view) {
        console.log('Changing calendar view to:', view);
        console.log('Previous view was:', this.calendarView);
        this.calendarView = view;
        console.log('Calling updateCalendar()...');
        console.log('this.updateCalendar exists:', typeof this.updateCalendar);
        console.log('this object in changeCalendarView:', this);
        
        try {
            if (typeof this.updateCalendar === 'function') {
                this.updateCalendar();
                console.log('updateCalendar() called successfully');
            } else {
                console.error('updateCalendar is not a function!');
                console.log('Available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(this)));
            }
        } catch (error) {
            console.error('Error calling updateCalendar():', error);
        }
        
        // Update button states
        document.querySelectorAll('.calendar-view-btn').forEach(btn => {
            btn.classList.remove('btn-primary');
            btn.classList.add('btn-outline-secondary');
        });
        
        const activeBtn = document.querySelector(`[data-view="${view}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('btn-outline-secondary');
            activeBtn.classList.add('btn-primary');
        }
        console.log('changeCalendarView() completed');
    }
    
    previousMonth() {
        console.log('Previous month clicked');
        if (!this.currentDate) {
            console.log('currentDate not initialized, initializing...');
            this.currentDate = new Date();
        }
        console.log('Date before:', this.currentDate.toLocaleDateString());
        this.currentDate.setMonth(this.currentDate.getMonth() - 1);
        console.log('Date after:', this.currentDate.toLocaleDateString());
        console.log('Calling updateCalendar()...');
        try {
            this.updateCalendar();
            console.log('updateCalendar() called successfully');
        } catch (error) {
            console.error('Error calling updateCalendar():', error);
        }
    }
    
    nextMonth() {
        console.log('Next month clicked');
        if (!this.currentDate) {
            console.log('currentDate not initialized, initializing...');
            this.currentDate = new Date();
        }
        console.log('Date before:', this.currentDate.toLocaleDateString());
        this.currentDate.setMonth(this.currentDate.getMonth() + 1);
        console.log('Date after:', this.currentDate.toLocaleDateString());
        console.log('Calling updateCalendar()...');
        try {
            this.updateCalendar();
            console.log('updateCalendar() called successfully');
        } catch (error) {
            console.error('Error calling updateCalendar():', error);
        }
    }
    
    previousWeek() {
        console.log('Previous week clicked');
        if (!this.currentDate) {
            console.log('currentDate not initialized, initializing...');
            this.currentDate = new Date();
        }
        console.log('Date before:', this.currentDate.toLocaleDateString());
        this.currentDate.setDate(this.currentDate.getDate() - 7);
        console.log('Date after:', this.currentDate.toLocaleDateString());
        console.log('Calling updateCalendar()...');
        try {
            this.updateCalendar();
            console.log('updateCalendar() called successfully');
        } catch (error) {
            console.error('Error calling updateCalendar():', error);
        }
    }
    
    previousDay() {
        console.log('Previous day clicked');
        if (!this.currentDate) {
            this.currentDate = new Date();
        }
        this.currentDate.setDate(this.currentDate.getDate() - 1);
        try {
            this.updateCalendar();
        } catch (error) {
            console.error('Error calling updateCalendar():', error);
        }
    }
    
    nextDay() {
        console.log('Next day clicked');
        if (!this.currentDate) {
            this.currentDate = new Date();
        }
        this.currentDate.setDate(this.currentDate.getDate() + 1);
        try {
            this.updateCalendar();
        } catch (error) {
            console.error('Error calling updateCalendar():', error);
        }
    }

    nextWeek() {
        console.log('Next week clicked');
        if (!this.currentDate) {
            console.log('currentDate not initialized, initializing...');
            this.currentDate = new Date();
        }
        console.log('Date before:', this.currentDate.toLocaleDateString());
        this.currentDate.setDate(this.currentDate.getDate() + 7);
        console.log('Date after:', this.currentDate.toLocaleDateString());
        console.log('Calling updateCalendar()...');
        try {
            this.updateCalendar();
            console.log('updateCalendar() called successfully');
        } catch (error) {
            console.error('Error calling updateCalendar():', error);
        }
    }
    
    selectEventFromCalendar(event) {
        console.log('Event selected from calendar:', event.title);
        
        // Show event details modal
        this.showEventDetails(event);
        
        // Highlight the corresponding event in the left panel
        this.highlightEventInList(event.id);
        
        // Scroll to the event in the left panel
        this.scrollToEventInList(event.id);
    }
    
    highlightEventInList(eventId) {
        // Remove previous highlights
        document.querySelectorAll('.event-item').forEach(item => {
            item.classList.remove('highlighted-event');
        });
        
        // Add highlight to the selected event
        const eventItem = document.querySelector(`[data-event-id="${eventId}"]`);
        if (eventItem) {
            eventItem.classList.add('highlighted-event');
        }
    }
    
    scrollToEventInList(eventId) {
        const eventItem = document.querySelector(`[data-event-id="${eventId}"]`);
        if (eventItem) {
            eventItem.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
        }
    }
    
    setupCalendarEventListeners() {
        console.log('Setting up calendar event listeners...');
        
        // Remove any existing listeners to avoid duplicates
        if (this.calendarClickHandler) {
            document.removeEventListener('click', this.calendarClickHandler);
        }
        
        // Create the event handler
        this.calendarClickHandler = (e) => {
            console.log('Click event detected on:', e.target);
            
            // Calendar navigation buttons
            if (e.target.closest('.calendar-nav-btn')) {
                const button = e.target.closest('.calendar-nav-btn');
                const action = button.getAttribute('data-action');
                
                console.log('Calendar navigation clicked:', action);
                
                if (action === 'previous') {
                    if (this.calendarView === 'month') {
                        this.previousMonth();
                    } else if (this.calendarView === 'week') {
                        this.previousWeek();
                    } else if (this.calendarView === 'day') {
                        this.previousDay();
                    }
                } else if (action === 'next') {
                    if (this.calendarView === 'month') {
                        this.nextMonth();
                    } else if (this.calendarView === 'week') {
                        this.nextWeek();
                    } else if (this.calendarView === 'day') {
                        this.nextDay();
                    }
                }
            }
            
            // Calendar view toggle buttons
            if (e.target.closest('.calendar-view-btn')) {
                e.preventDefault();
                const button = e.target.closest('.calendar-view-btn');
                const view = button.getAttribute('data-view');
                if (view) {
                    console.log('Calendar view toggle clicked:', view);
                    this.changeCalendarView(view);
                }
            }
            
            // Click on a day cell in month view -> go to that week
            if (this.calendarView === 'month' && e.target.closest('.calendar-day')) {
                const cell = e.target.closest('.calendar-day');
                const iso = cell.getAttribute('data-date');
                if (iso) {
                    this.currentDate = new Date(iso);
                    this.changeCalendarView('week');
                }
            }

            // Click on a day header in week view -> go to that day
            if (this.calendarView === 'week' && e.target.closest('.calendar-week-day-header')) {
                const header = e.target.closest('.calendar-week-day-header');
                const iso = header.getAttribute('data-date');
                if (iso) {
                    this.currentDate = new Date(iso);
                    this.changeCalendarView('day');
                }
            }

            // Click anywhere in a week's day column (not on an event) -> go to that day
            if (this.calendarView === 'week' && !e.target.closest('.time-event') && e.target.closest('.time-grid-content')) {
                const content = e.target.closest('.time-grid-content');
                const rect = content.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const dayWidth = rect.width / 7;
                if (dayWidth > 0) {
                    let dayIndex = Math.floor(x / dayWidth);
                    if (dayIndex < 0) dayIndex = 0;
                    if (dayIndex > 6) dayIndex = 6;
                    const weekStart = this.getWeekStart(this.currentDate);
                    const clickedDate = new Date(weekStart);
                    clickedDate.setDate(clickedDate.getDate() + dayIndex);
                    this.currentDate = clickedDate;
                    this.changeCalendarView('day');
                }
            }

            // Calendar event clicks (month view tiles)
            if (e.target.closest('.calendar-event')) {
                const eventElement = e.target.closest('.calendar-event');
                const eventData = eventElement.getAttribute('data-event');
                if (eventData) {
                    try {
                        const event = JSON.parse(eventData);
                        console.log('Calendar event clicked:', event.title);
                        this.selectEventFromCalendar(event);
                    } catch (error) {
                        console.error('Error parsing event data:', error);
                    }
                }
            }

            // Time-grid event clicks (week/day views)
            if (e.target.closest('.time-event')) {
                const eventElement = e.target.closest('.time-event');
                const eventData = eventElement.getAttribute('data-event');
                if (eventData) {
                    try {
                        const event = JSON.parse(eventData);
                        console.log('Time-grid event clicked:', event.title);
                        this.selectEventFromCalendar(event);
                    } catch (error) {
                        console.error('Error parsing event data:', error);
                    }
                }
            }
        };
        
        // Add the event listener
        document.addEventListener('click', this.calendarClickHandler);
        console.log('Calendar event listeners set up successfully');
    }
    
    debugCalendarButtons() {
        console.log('=== Debugging Calendar Buttons ===');
        
        const calendarContainer = document.getElementById('calendarContainer');
        if (!calendarContainer) {
            console.log('❌ Calendar container not found');
            return;
        }
        
        // Check navigation buttons
        const navButtons = calendarContainer.querySelectorAll('.calendar-nav-btn');
        console.log(`Navigation buttons found: ${navButtons.length}`);
        navButtons.forEach((btn, index) => {
            console.log(`Nav button ${index + 1}:`, {
                action: btn.getAttribute('data-action'),
                text: btn.textContent.trim(),
                classes: btn.className,
                visible: btn.offsetParent !== null
            });
        });
        
        // Check view toggle buttons
        const viewButtons = document.querySelectorAll('.calendar-view-btn');
        console.log(`View toggle buttons found: ${viewButtons.length}`);
        viewButtons.forEach((btn, index) => {
            console.log(`View button ${index + 1}:`, {
                view: btn.getAttribute('data-view'),
                text: btn.textContent.trim(),
                classes: btn.className,
                visible: btn.offsetParent !== null
            });
        });
        
        console.log('=== End Debug ===');
    }
}

// Global function for calendar downloads
function downloadCalendar(filterType) {
    const url = `/api/calendar/${filterType}`;
    
    // Create a temporary link and trigger download
    const link = document.createElement('a');
    link.href = url;
    link.download = `aiplusbio_${filterType}_events.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Show success message
    showSuccessNotification(`Calendar file downloaded! Import it into your calendar app.`);
}

// Global notification function
function showSuccessNotification(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new EventsApp();
}); 