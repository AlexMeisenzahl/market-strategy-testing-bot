# Mobile Setup Guide

## Installing as an iPhone App

The Market Strategy Bot Dashboard can be installed as a Progressive Web App (PWA) on your iPhone, providing a native app-like experience.

### Prerequisites

- iOS 15.0 or later (iOS 16+ recommended for best experience)
- Safari browser (required for installation)
- Network access to your bot's dashboard

### Installation Steps

#### 1. Open Dashboard in Safari

1. Open Safari on your iPhone
2. Navigate to your dashboard URL (e.g., `http://your-server:5000`)
3. Wait for the page to fully load

#### 2. Add to Home Screen

1. Tap the **Share** button (square with arrow pointing up) at the bottom of Safari
2. Scroll down and tap **"Add to Home Screen"**
3. Edit the name if desired (default: "Market Bot")
4. Tap **"Add"** in the top right corner

#### 3. Launch the App

1. Find the app icon on your Home Screen
2. Tap to open
3. The app will open full-screen without Safari's browser bars

### Features Available on iPhone

#### ✅ Native App Experience
- Full-screen display (no browser bars)
- Appears in app switcher
- Works with iOS gestures (swipe up to close, etc.)
- Respects iPhone notch and safe areas

#### ✅ Optimized Mobile UI
- Bottom navigation bar with 5 main tabs
- Touch-friendly buttons (44x44px minimum)
- Swipe gestures for navigation
- Pull-to-refresh on all pages
- Card layouts instead of tables

#### ✅ Offline Support
- Works without internet connection (cached data)
- Automatic sync when reconnected
- Offline fallback page with retry option

#### ✅ iOS Integration
- Haptic feedback on button taps
- iOS keyboard optimizations
- Status bar color matching
- Splash screens for all iPhone models

### Navigation Guide

#### Bottom Navigation Bar (Main)
- 🏠 **Home** - Overview dashboard
- 💱 **Trades** - Trading history
- 🎮 **Control** - Bot control panel
- 📈 **Analytics** - Performance analytics
- ☰ **More** - Opens slide-out menu

#### Slide-Out Menu (Secondary)
- 💡 Opportunities - Market opportunities
- 📄 Tax Reports - Tax exports
- ⚙️ Settings - App settings

#### Gestures
- **Swipe left** from edge - Open menu
- **Swipe right** - Close menu
- **Pull down** at top - Refresh page
- **Tap status bar** - Scroll to top

### Troubleshooting

#### App Won't Install
**Problem:** "Add to Home Screen" option missing
**Solution:** 
- Make sure you're using Safari (not Chrome or Firefox)
- Update iOS to latest version
- Clear Safari cache and try again

#### App Shows Safari Bars
**Problem:** Browser bars visible in app
**Solution:**
- Delete the app from Home Screen
- Re-add using "Add to Home Screen" in Safari
- Ensure the manifest.json file is accessible

#### Offline Mode Not Working
**Problem:** App shows errors when offline
**Solution:**
- Open the app while online first
- Wait for initial data to cache
- Check that service worker is registered (check console)

#### Icons Not Showing
**Problem:** Default iOS icon appears instead of custom icon
**Solution:**
- Force refresh the page (pull down when at top)
- Delete and reinstall the app
- Check that icon files are accessible

#### App Feels Slow
**Problem:** Animations are laggy
**Solution:**
- Close other apps to free memory
- Restart your iPhone
- Clear app cache by reinstalling

### Performance Tips

#### For Best Experience:
1. **Use on iOS 16+** for latest PWA features
2. **Connect via Tailscale** for secure remote access
3. **Enable WiFi** for faster data loading
4. **Close when not in use** to save battery
5. **Update regularly** by reinstalling from Safari

#### Battery Usage:
- The app uses minimal battery when idle
- Real-time updates consume more power
- Consider disabling auto-refresh for battery saving

### Uninstalling

To remove the app:
1. Long-press the app icon on Home Screen
2. Tap **"Remove App"**
3. Select **"Delete App"**
4. Confirm deletion

### Advanced Features

#### Notifications (Future)
The PWA framework supports push notifications. This feature will be enabled in a future update once backend notification support is configured.

#### Background Sync (Future)
Automatic background data synchronization will be available in a future update.

#### Share Target (Future)
Share market opportunities directly to the app from other apps.

### Security Notes

- The app runs in a sandboxed environment
- No data is shared with third parties
- All data is stored locally on your device
- Use HTTPS in production for secure connections

### Getting Help

If you encounter issues:
1. Check the troubleshooting section above
2. Verify server connectivity
3. Review browser console for errors
4. Contact support with error details

### Version Information

- PWA Version: 2.0
- Minimum iOS: 15.0
- Recommended iOS: 16.0+
- Last Updated: February 2026
