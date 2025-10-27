// Final Calendar Debug Script
// Run this in the browser console at http://localhost:5001

console.log('🔍 FINAL Calendar Debug Script');
console.log('=' * 50);

// Test 1: Check app availability
console.log('1. App availability:', typeof window.app !== 'undefined');
if (window.app) {
    console.log('   - App events:', window.app.events.length);
    console.log('   - App filtered events:', window.app.filteredEvents.length);
    console.log('   - App calendar view:', window.app.calendarView);
    console.log('   - App current date:', window.app.currentDate);
}

// Test 2: Check calendar container
const calendarContainer = document.getElementById('calendarContainer');
console.log('2. Calendar container:', !!calendarContainer);
if (calendarContainer) {
    console.log('   - Container HTML length:', calendarContainer.innerHTML.length);
    console.log('   - Container classes:', calendarContainer.className);
}

// Test 3: Check toggle buttons
const toggleButtons = document.querySelectorAll('.calendar-view-btn');
console.log('3. Toggle buttons found:', toggleButtons.length);
toggleButtons.forEach((btn, i) => {
    console.log(`   - Button ${i}:`, btn.textContent.trim(), 'data-view:', btn.getAttribute('data-view'));
});

// Test 4: Check navigation buttons
const navButtons = document.querySelectorAll('.calendar-nav-btn');
console.log('4. Navigation buttons found:', navButtons.length);
navButtons.forEach((btn, i) => {
    console.log(`   - Nav button ${i}:`, btn.getAttribute('data-action'));
});

// Test 5: Test calendar functions
if (window.app) {
    console.log('5. Testing calendar functions...');
    
    // Test view change
    console.log('   - Testing changeCalendarView...');
    try {
        const originalView = window.app.calendarView;
        window.app.changeCalendarView('week');
        console.log('   - ✅ changeCalendarView worked, new view:', window.app.calendarView);
        
        // Change back
        window.app.changeCalendarView('month');
        console.log('   - ✅ changeCalendarView back to month worked');
    } catch (e) {
        console.error('   - ❌ changeCalendarView failed:', e);
    }
    
    // Test navigation
    console.log('   - Testing navigation...');
    try {
        const originalDate = new Date(window.app.currentDate);
        window.app.previousMonth();
        console.log('   - ✅ previousMonth worked');
        
        // Reset
        window.app.currentDate = originalDate;
        window.app.updateCalendar();
    } catch (e) {
        console.error('   - ❌ previousMonth failed:', e);
    }
}

// Test 6: Check for errors
console.log('6. Checking for errors...');
const errors = [];
window.addEventListener('error', (e) => {
    errors.push(e.error);
    console.error('   - JavaScript error:', e.error);
});

// Test 7: Manual test instructions
console.log('7. Manual testing instructions:');
console.log('   - Click "Week" button - should see:');
console.log('     * "Calendar view toggle clicked: week"');
console.log('     * "Changing calendar view to: week"');
console.log('     * "Calendar view is: week"');
console.log('     * "Rendering week view..."');
console.log('   - Click "Month" button - should see similar messages');
console.log('   - Click navigation arrows - should see:');
console.log('     * "Calendar navigation clicked: previous/next"');
console.log('     * "Previous/Next month clicked"');

console.log('=' * 50);
console.log('🔍 Debug script completed. Check console for results.'); 