# Calendar Debug Guide

## 🎯 **How to Debug the Calendar Issues**

### **Step 1: Open the Application**
1. Go to http://localhost:5001
2. Open Developer Tools (F12 or right-click → Inspect)
3. Go to the Console tab

### **Step 2: Check Initialization**
Look for these messages in the console:
- ✅ `EventsApp constructor called`
- ✅ `EventsApp init started`
- ✅ `Loaded X events`
- ✅ `Updating calendar with X events`
- ✅ `Rendering month view...`
- ✅ `Month name: [Month Year]`
- ✅ `Setting up calendar event listeners...`
- ✅ `Calendar event listeners set up successfully`

### **Step 3: Run the Debug Script**
Copy and paste this into the browser console:

```javascript
// Debug script for calendar functionality
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
```

### **Step 4: Manual Testing**

#### **Test Navigation Arrows:**
1. Look for navigation arrows in the calendar header
2. Click the left arrow (should go to previous month)
3. Click the right arrow (should go to next month)
4. Check console for: `Calendar navigation clicked: previous/next`

#### **Test Month/Week Toggle:**
1. Look for "Month" and "Week" buttons in the calendar header
2. Click "Week" button (should switch to week view)
3. Click "Month" button (should switch back to month view)
4. Check console for: `Calendar view toggle clicked: month/week`

#### **Test Calendar Event Clicking:**
1. Look for events in the calendar (colored boxes)
2. Click on any event
3. Check if:
   - Event details modal opens
   - Corresponding event in left panel gets highlighted (blue background)
   - Console shows: `Calendar event clicked: [event title]`

### **Step 5: Report Issues**

**If you see errors, please report:**
1. **Console errors** (red text in console)
2. **Missing log messages** (which ones don't appear)
3. **What happens when you click buttons** (nothing, errors, etc.)
4. **Screenshot** of the calendar area

### **Step 6: Common Issues & Solutions**

#### **Issue: "App available: false"**
- **Cause**: JavaScript not loading properly
- **Solution**: Refresh the page and check for JavaScript errors

#### **Issue: "Calendar container exists: false"**
- **Cause**: Calendar not being generated
- **Solution**: Check if events are loading properly

#### **Issue: Buttons not responding**
- **Cause**: Event listeners not set up
- **Solution**: Check console for "Calendar event listeners set up successfully"

#### **Issue: Calendar events not highlighting**
- **Cause**: Event data not properly stored
- **Solution**: Check if events have `data-event` attributes

## 🚨 **Emergency Debug Commands**

If nothing works, try these in the console:

```javascript
// Force calendar update
if (window.app) {
    window.app.updateCalendar();
}

// Force event listener setup
if (window.app) {
    window.app.setupCalendarEventListeners();
}

// Test specific functions
if (window.app) {
    window.app.previousMonth();
    window.app.changeCalendarView('week');
}
```

## 📞 **Need Help?**

If you're still having issues, please provide:
1. **Console output** (copy all messages)
2. **Screenshot** of the calendar area
3. **What you tried** and what happened
4. **Browser** and **version** you're using 