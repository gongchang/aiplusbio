document.addEventListener('DOMContentLoaded', () => {
    const refreshBtn = document.getElementById('refreshVirtualEventsBtn');
    const statusEl = document.getElementById('virtualWorldwideStatus');
    const gridEl = document.getElementById('virtualEventsGrid');

    if (!refreshBtn || !statusEl || !gridEl) {
        return;
    }

    const originalMarkup = gridEl.innerHTML;

    const resetStatusClasses = () => {
        statusEl.classList.remove('alert-info', 'alert-success', 'alert-warning', 'alert-danger');
    };

    const showStatus = (message, tone = 'info') => {
        resetStatusClasses();
        statusEl.classList.remove('d-none');
        statusEl.classList.add(`alert-${tone}`);
        statusEl.textContent = message;
    };

    const hideStatus = () => {
        statusEl.classList.add('d-none');
    };

    const createBadge = (type) => {
        const badge = document.createElement('span');
        badge.className = 'badge event-type-badge';

        if (type === 'youtube') {
            badge.classList.add('youtube-badge');
            badge.innerHTML = '<i class="fab fa-youtube me-1"></i>YOUTUBE';
        } else {
            badge.classList.add('seminar-badge');
            badge.innerHTML = '<i class="fas fa-chalkboard-teacher me-1"></i>SEMINAR';
        }

        return badge;
    };

    const trimDescription = (description = '') => {
        if (!description) {
            return 'Visit the source for more information about this virtual event.';
        }
        const cleaned = description.replace(/\s+/g, ' ').trim();
        return cleaned.length > 220 ? `${cleaned.slice(0, 217)}…` : cleaned;
    };

    const createCard = (event) => {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';

        const card = document.createElement('div');
        card.className = 'card virtual-event-card h-100';

        const body = document.createElement('div');
        body.className = 'card-body d-flex flex-column';

        const badgeContainer = document.createElement('div');
        badgeContainer.className = 'd-flex justify-content-between align-items-start mb-3';
        badgeContainer.appendChild(createBadge(event.type));

        const title = document.createElement('h5');
        title.className = 'card-title';
        title.textContent = event.title || 'Virtual Event';

        const description = document.createElement('p');
        description.className = 'card-text text-muted';
        description.textContent = trimDescription(event.description);

        const buttonContainer = document.createElement('div');
        buttonContainer.className = 'mt-auto';

        const link = document.createElement('a');
        link.className = 'btn btn-outline-primary btn-sm';
        link.href = event.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.innerHTML = '<i class="fas fa-external-link-alt me-1"></i>Visit Site';
        if (event.type === 'youtube') {
            link.innerHTML = '<i class="fas fa-external-link-alt me-1"></i>Visit Channel';
        }

        buttonContainer.appendChild(link);

        body.appendChild(badgeContainer);
        body.appendChild(title);
        body.appendChild(description);
        body.appendChild(buttonContainer);

        card.appendChild(body);
        col.appendChild(card);
        return col;
    };

    const renderEvents = (events) => {
        if (!Array.isArray(events) || !events.length) {
            gridEl.innerHTML = originalMarkup;
            showStatus('No additional events were returned from the latest list.', 'warning');
            return;
        }

        gridEl.innerHTML = '';
        events.forEach((event) => {
            try {
                gridEl.appendChild(createCard(event));
            } catch (err) {
                console.error('Failed to render event card', err, event);
            }
        });

        showStatus(`Loaded ${events.length} virtual resources from the latest list.`, 'success');
    };

    const fetchEvents = async () => {
        try {
            const response = await fetch('/api/virtual-worldwide');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Failed to load events');
            }
            return data.events || [];
        } catch (error) {
            console.error('Error loading virtual worldwide events:', error);
            throw error;
        }
    };

    refreshBtn.addEventListener('click', async () => {
        const originalButtonMarkup = refreshBtn.innerHTML;
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Refreshing...';
        showStatus('Fetching latest virtual events…', 'info');

        try {
            const events = await fetchEvents();
            renderEvents(events);
        } catch (error) {
            showStatus('Unable to load events right now. Please try again later.', 'danger');
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = originalButtonMarkup;
        }
    });
});
