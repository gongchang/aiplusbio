// Debug script for calendar navigation
console.log('=== Calendar Navigation Debug ===');

// Check if app exists
if (typeof window.app !== 'undefined') {
    console.log('✅ App object found');
    console.log('App state:', {
        events: window.app.filteredEvents?.length || 0,
        calendarView: window.app.calendarView,
        currentDate: window.app.currentDate
    });
} else {
    console.log('❌ App object not found');
}

// Check if calendar container exists
const calendarContainer = document.getElementById('calendarContainer');
if (calendarContainer) {
    console.log('✅ Calendar container found');
    console.log('Calendar container HTML length:', calendarContainer.innerHTML.length);
    
    // Check for navigation buttons
    const navButtons = calendarContainer.querySelectorAll('.calendar-nav-btn');
    console.log('Navigation buttons found:', navButtons.length);
    
    navButtons.forEach((btn, index) => {
        console.log(`Button ${index + 1}:`, {
            action: btn.getAttribute('data-action'),
            text: btn.textContent.trim(),
            classes: btn.className
        });
    });
    
    // Check for view toggle buttons
    const viewButtons = document.querySelectorAll('.calendar-view-btn');
    console.log('View toggle buttons found:', viewButtons.length);
    
    viewButtons.forEach((btn, index) => {
        console.log(`View button ${index + 1}:`, {
            view: btn.getAttribute('data-view'),
            text: btn.textContent.trim(),
            classes: btn.className
        });
    });
    
} else {
    console.log('❌ Calendar container not found');
}

// Test manual navigation
console.log('\n=== Testing Manual Navigation ===');

// Test previous month
if (window.app && window.app.previousMonth) {
    console.log('Testing previousMonth()...');
    const originalDate = new Date(window.app.currentDate);
    window.app.previousMonth();
    console.log('Date before:', originalDate.toLocaleDateString());
    console.log('Date after:', window.app.currentDate.toLocaleDateString());
}

// Test next month
if (window.app && window.app.nextMonth) {
    console.log('Testing nextMonth()...');
    const originalDate = new Date(window.app.currentDate);
    window.app.nextMonth();
    console.log('Date before:', originalDate.toLocaleDateString());
    console.log('Date after:', window.app.currentDate.toLocaleDateString());
}

// Test view toggle
if (window.app && window.app.changeCalendarView) {
    console.log('Testing changeCalendarView()...');
    const originalView = window.app.calendarView;
    window.app.changeCalendarView(originalView === 'month' ? 'week' : 'month');
    console.log('View before:', originalView);
    console.log('View after:', window.app.calendarView);
}

console.log('=== Debug Complete ==='); 