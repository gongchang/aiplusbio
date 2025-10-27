// Debug script for calendar functionality
// Run this in the browser console at http://localhost:5001

console.log('🔍 Calendar Debug Script Started');

// Test 1: Check if app is available
console.log('App available:', typeof window.app !== 'undefined');
if (window.app) {
    console.log('App events:', window.app.events.length);
    console.log('App filtered events:', window.app.filteredEvents.length);
    console.log('App calendar view:', window.app.calendarView);
    console.log('App current date:', window.app.currentDate);
}

// Test 2: Check if calendar container exists
const calendarContainer = document.getElementById('calendarContainer');
console.log('Calendar container exists:', !!calendarContainer);
if (calendarContainer) {
    console.log('Calendar container HTML:', calendarContainer.innerHTML.substring(0, 200) + '...');
}

// Test 3: Test calendar functions directly
if (window.app) {
    console.log('Testing calendar functions...');
    
    // Test navigation
    console.log('Testing previousMonth...');
    try {
        window.app.previousMonth();
        console.log('✅ previousMonth worked');
    } catch (e) {
        console.error('❌ previousMonth failed:', e);
    }
    
    // Test view change
    console.log('Testing changeCalendarView...');
    try {
        window.app.changeCalendarView('week');
        console.log('✅ changeCalendarView worked');
    } catch (e) {
        console.error('❌ changeCalendarView failed:', e);
    }
}

// Test 4: Check for event listeners
console.log('Checking for event listeners...');
const buttons = document.querySelectorAll('button');
console.log('Found buttons:', buttons.length);
buttons.forEach((btn, i) => {
    console.log(`Button ${i}:`, btn.textContent.trim(), 'onclick:', btn.onclick);
});

console.log('🔍 Calendar Debug Script Completed'); 