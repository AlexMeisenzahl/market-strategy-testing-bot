# Mobile Testing Checklist

## Overview

This checklist ensures the mobile dashboard and PWA functionality work correctly across different devices and scenarios.

## Test Devices

- [ ] iPhone SE (small screen, 640x1136)
- [ ] iPhone 14 Pro (standard, 1170x2532)
- [ ] iPhone 14 Pro Max (large, 1284x2778)
- [ ] iPad (tablet, 1024x768+)
- [ ] Desktop browser (1920x1080+)

---

## 1. Device Detection Tests

### Device Type Detection
- [ ] Mobile devices show mobile UI (bottom nav, top bar)
- [ ] Tablets show tablet-optimized layout
- [ ] Desktop shows desktop navigation
- [ ] Body has correct device class (`device-mobile`, `device-tablet`, `device-desktop`)

### OS Detection
- [ ] iOS devices get `ios-device` class
- [ ] Android devices get `android-device` class
- [ ] Haptic feedback works on iOS

### PWA Detection
- [ ] Installed app gets `standalone-app` class
- [ ] Standalone mode hides Safari-specific UI
- [ ] Browser mode shows normal navigation

### Safe Area Detection
- [ ] iPhone X+ gets `has-safe-area` class
- [ ] Top bar respects notch area
- [ ] Bottom nav respects home indicator

---

## 2. Navigation Tests

### Bottom Navigation Bar (Mobile Only)
- [ ] Shows 5 items: Home, Trades, Control, Analytics, More
- [ ] Icons are clear and touch-friendly (44x44px)
- [ ] Labels are visible and readable
- [ ] Active page is highlighted
- [ ] Tapping items changes pages
- [ ] Navigation is fixed at bottom
- [ ] Respects safe area insets

### Mobile Top Bar
- [ ] Shows hamburger menu button
- [ ] Shows app logo in center
- [ ] Shows connection status
- [ ] Fixed at top of screen
- [ ] Respects notch on iPhone X+

### Hamburger Slide-Out Menu
- [ ] Opens on hamburger button tap
- [ ] Opens on "More" bottom nav tap
- [ ] Opens on swipe right from left edge
- [ ] Closes on backdrop tap
- [ ] Closes on link tap
- [ ] Closes on swipe left
- [ ] Shows all secondary pages
- [ ] Active page is highlighted
- [ ] Smooth slide animation

### Desktop Navigation
- [ ] Hidden on mobile (<768px)
- [ ] Visible on tablet and desktop
- [ ] All links work correctly
- [ ] Responsive to screen size changes

---

## 3. Touch Interaction Tests

### Tap Targets
- [ ] All buttons are minimum 44x44px
- [ ] Links are easy to tap
- [ ] No accidental double-taps
- [ ] Forms don't zoom on iOS (16px+ font)

### Swipe Gestures
- [ ] Swipe right from edge opens menu
- [ ] Swipe left closes menu
- [ ] Vertical scroll works normally
- [ ] Doesn't interfere with page scrolling

### Pull-to-Refresh
- [ ] Pull down at top triggers refresh
- [ ] Visual indicator appears
- [ ] Data refreshes successfully
- [ ] Works on all pages
- [ ] Doesn't conflict with scroll

### Haptic Feedback (iOS)
- [ ] Button taps trigger light haptic
- [ ] Important actions trigger medium haptic
- [ ] Errors trigger heavy haptic
- [ ] No lag or delay in feedback

---

## 4. Layout Tests

### Mobile Layout (< 768px)
- [ ] Single column layout
- [ ] Full-width cards
- [ ] Adequate padding (12-16px)
- [ ] No horizontal overflow
- [ ] Content below top bar
- [ ] Content above bottom nav
- [ ] Safe area respected

### Tablet Layout (768-1024px)
- [ ] Two column layout
- [ ] Optimized spacing
- [ ] Touch-friendly elements
- [ ] No mobile bottom nav
- [ ] Desktop nav visible

### Desktop Layout (> 1024px)
- [ ] Multi-column layout
- [ ] Full desktop navigation
- [ ] No mobile elements visible
- [ ] Unchanged from before

### Orientation Changes
- [ ] Portrait mode works correctly
- [ ] Landscape mode adjusts properly
- [ ] Navigation stays accessible
- [ ] No layout breaks

---

## 5. Component Tests

### Tables
- [ ] Hidden on mobile
- [ ] Replaced with card view
- [ ] Cards show essential data
- [ ] Cards are touch-friendly
- [ ] Expandable for full details
- [ ] Visible as tables on desktop

### Charts
- [ ] Reduced to 250px height on mobile
- [ ] Legends stack appropriately
- [ ] Tooltips are readable
- [ ] Touch controls work
- [ ] Zoom and pan work (if enabled)
- [ ] Full size on desktop

### Forms
- [ ] Full-width inputs
- [ ] 16px+ font size (no zoom)
- [ ] Appropriate keyboard types
- [ ] Good spacing between fields
- [ ] Submit buttons are prominent
- [ ] Labels are clear

### Modals
- [ ] Full-screen on mobile
- [ ] Slide-up animation
- [ ] Sticky header with close button
- [ ] Scrollable content
- [ ] Sticky footer with actions
- [ ] Full-width buttons
- [ ] Normal size on desktop

### Stat Cards
- [ ] Compact on mobile
- [ ] Clear large numbers
- [ ] Icons visible
- [ ] Good contrast
- [ ] Touch-friendly

---

## 6. PWA Functionality Tests

### Installation (iOS)
- [ ] "Add to Home Screen" option available
- [ ] Custom icon appears
- [ ] Custom name appears
- [ ] Splash screen shows on launch
- [ ] Correct splash for device model

### Installation (Android)
- [ ] Install prompt appears
- [ ] Custom icon appears
- [ ] Custom name appears
- [ ] Splash screen shows

### Standalone Mode
- [ ] Opens full-screen
- [ ] No browser bars
- [ ] Status bar styled correctly
- [ ] Back button works (Android)
- [ ] iOS gestures work

### Manifest
- [ ] Manifest.json accessible at /manifest.json
- [ ] Correct name and short_name
- [ ] Correct colors (theme, background)
- [ ] All icon sizes present
- [ ] Display mode is "standalone"

### Service Worker
- [ ] Registers successfully
- [ ] Accessible at /service-worker.js
- [ ] Caches static assets
- [ ] Updates cache on new version
- [ ] No console errors

---

## 7. Offline Functionality Tests

### Initial Load
- [ ] Service worker installs
- [ ] Static assets cached
- [ ] App shell cached
- [ ] Can view cached pages offline

### Offline Mode
- [ ] Offline page appears when disconnected
- [ ] Cached data still visible
- [ ] "You're offline" message shows
- [ ] Retry button works

### Coming Back Online
- [ ] Automatic reconnection detected
- [ ] Data syncs automatically
- [ ] Updates apply successfully
- [ ] No data loss

### Cache Management
- [ ] Old caches deleted on update
- [ ] Cache size reasonable
- [ ] Can clear cache
- [ ] Fresh data loads after reconnect

---

## 8. Performance Tests

### Load Time
- [ ] Initial load < 3 seconds
- [ ] Subsequent loads < 1 second
- [ ] Service worker speeds up loads
- [ ] Images load progressively

### Animations
- [ ] 60fps animations (smooth)
- [ ] No jank or stutter
- [ ] GPU acceleration working
- [ ] Reduced motion respected

### Memory Usage
- [ ] No memory leaks
- [ ] Reasonable memory footprint
- [ ] Doesn't crash on low memory
- [ ] Charts don't consume excessive memory

### Battery Usage
- [ ] Minimal battery drain when idle
- [ ] Reasonable drain during use
- [ ] Auto-refresh can be disabled
- [ ] No excessive background activity

---

## 9. Accessibility Tests

### Screen Reader
- [ ] Navigation announced correctly
- [ ] Buttons have labels
- [ ] Forms have labels
- [ ] Page changes announced

### Keyboard Navigation
- [ ] Can tab through elements
- [ ] Focus indicators visible
- [ ] Enter/Space activate buttons
- [ ] Escape closes modals

### Reduced Motion
- [ ] Respects prefers-reduced-motion
- [ ] Animations simplified/removed
- [ ] Still fully functional

### Color Contrast
- [ ] Text readable on backgrounds
- [ ] Meets WCAG AA standards
- [ ] Important info not color-only

---

## 10. Integration Tests

### Page Navigation
- [ ] All pages load correctly
- [ ] Data updates properly
- [ ] No JavaScript errors
- [ ] Page state maintained

### Real-time Updates
- [ ] Trade updates appear
- [ ] Status changes update
- [ ] Charts update automatically
- [ ] Connection status accurate

### Bot Control
- [ ] Can start/stop bot from mobile
- [ ] Can pause/resume
- [ ] Emergency stop works
- [ ] Settings can be changed

### Data Refresh
- [ ] Manual refresh works
- [ ] Auto-refresh works
- [ ] Pull-to-refresh works
- [ ] No duplicate requests

---

## 11. Cross-Browser Tests

### Safari (iOS)
- [ ] All features work
- [ ] PWA installs correctly
- [ ] Service worker works
- [ ] No rendering issues

### Chrome (iOS)
- [ ] Displays correctly
- [ ] Navigation works
- [ ] Can't install as PWA (expected)

### Chrome (Android)
- [ ] All features work
- [ ] PWA installs correctly
- [ ] Service worker works
- [ ] Install banner appears

### Edge Mobile
- [ ] Displays correctly
- [ ] Navigation works
- [ ] PWA compatible

---

## 12. Network Condition Tests

### Fast Connection (WiFi)
- [ ] Everything loads quickly
- [ ] Real-time updates smooth
- [ ] Charts update rapidly

### Slow Connection (3G)
- [ ] Progressive loading
- [ ] Essential content first
- [ ] Loading indicators shown
- [ ] Still usable

### Intermittent Connection
- [ ] Handles disconnects gracefully
- [ ] Reconnects automatically
- [ ] No data corruption
- [ ] User notified of status

### Offline → Online
- [ ] Detects reconnection
- [ ] Syncs pending data
- [ ] Updates UI
- [ ] Clears offline indicator

---

## Test Results Template

### Test Run Information
- **Date:** _____________
- **Tester:** _____________
- **Build Version:** _____________
- **Device:** _____________
- **OS Version:** _____________
- **Browser:** _____________

### Summary
- **Tests Passed:** ____ / ____
- **Tests Failed:** ____
- **Critical Issues:** ____
- **Minor Issues:** ____

### Issues Found
1. _____________________________________________
2. _____________________________________________
3. _____________________________________________

### Notes
_________________________________________________
_________________________________________________
_________________________________________________

---

## Regression Tests

Run before each release:
- [ ] Device detection still works
- [ ] Navigation hasn't broken
- [ ] PWA still installs
- [ ] Offline mode works
- [ ] Desktop unchanged
- [ ] No new console errors
- [ ] Performance unchanged

---

**Version:** 1.0  
**Last Updated:** February 2026  
**Next Review:** March 2026
