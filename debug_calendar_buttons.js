// Debug script for calendar buttons
console.log('=== Calendar Button Debug ===');

// Check if app exists
if (typeof window.app !== 'undefined') {
    console.log('✅ App object found');
    
    // Test manual navigation
    console.log('Testing manual navigation...');
    const originalDate = new Date(window.app.currentDate);
    console.log('Original date:', originalDate.toLocaleDateString());
    
    // Test previous month
    if (window.app.previousMonth) {
        window.app.previousMonth();
        console.log('After previousMonth():', window.app.currentDate.toLocaleDateString());
    }
    
    // Test next month
    if (window.app.nextMonth) {
        window.app.nextMonth();
        console.log('After nextMonth():', window.app.currentDate.toLocaleDateString());
    }
    
    // Test view toggle
    if (window.app.changeCalendarView) {
        const originalView = window.app.calendarView;
        console.log('Original view:', originalView);
        window.app.changeCalendarView(originalView === 'month' ? 'week' : 'month');
        console.log('After changeCalendarView():', window.app.calendarView);
    }
    
} else {
    console.log('❌ App object not found');
}

// Check calendar container
const calendarContainer = document.getElementById('calendarContainer');
if (calendarContainer) {
    console.log('✅ Calendar container found');
    console.log('Container HTML length:', calendarContainer.innerHTML.length);
    
    // Check for navigation buttons
    const navButtons = calendarContainer.querySelectorAll('.calendar-nav-btn');
    console.log('Navigation buttons found:', navButtons.length);
    
    navButtons.forEach((btn, index) => {
        console.log(`Nav button ${index + 1}:`, {
            action: btn.getAttribute('data-action'),
            text: btn.textContent.trim(),
            classes: btn.className,
            visible: btn.offsetParent !== null,
            clickable: btn.style.pointerEvents !== 'none'
        });
        
        // Test click manually
        console.log(`Testing click on nav button ${index + 1}...`);
        btn.click();
    });
    
    // Check for view toggle buttons
    const viewButtons = document.querySelectorAll('.calendar-view-btn');
    console.log('View toggle buttons found:', viewButtons.length);
    
    viewButtons.forEach((btn, index) => {
        console.log(`View button ${index + 1}:`, {
            view: btn.getAttribute('data-view'),
            text: btn.textContent.trim(),
            classes: btn.className,
            visible: btn.offsetParent !== null,
            clickable: btn.style.pointerEvents !== 'none'
        });
        
        // Test click manually
        console.log(`Testing click on view button ${index + 1}...`);
        btn.click();
    });
    
} else {
    console.log('❌ Calendar container not found');
}

// Test event delegation
console.log('Testing event delegation...');
document.addEventListener('click', (e) => {
    console.log('Click event on:', e.target);
    if (e.target.closest('.calendar-nav-btn')) {
        console.log('✅ Navigation button click detected');
    }
    if (e.target.closest('.calendar-view-btn')) {
        console.log('✅ View button click detected');
    }
});

console.log('=== Debug Complete ===');
console.log('Now try clicking the calendar buttons and watch for console messages...'); 