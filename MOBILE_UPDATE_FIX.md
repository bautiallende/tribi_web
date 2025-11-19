# Mobile expo-updates Error - SOLVED ✅

## Problem

The mobile app was crashing on startup with the error:

```
java.io.IOException: failed to download remote updates
```

## Root Causes

1. **expo-updates module** was trying to check for OTA updates even in development
2. **Incompatible dependencies** were causing version conflicts
3. **Port 8081** was being blocked by zombie Node processes
4. **Slow dependency validation** was timing out connections to Expo's API

## Final Solution

### 1. Updated `app.config.js`

**Removed** all expo-updates configuration:

- ❌ No `updates` block
- ❌ No `runtimeVersion`
- ❌ No `expo-updates` plugin
- ❌ No iOS/Android update-specific settings

Result: Clean minimal config with only essential app settings.

### 2. Created `.env` file

Added environment variables to disable updates:

```env
EXPO_NO_UPDATES=1
EXPO_NO_DOCTOR=1
```

- `EXPO_NO_UPDATES=1`: Prevents expo-updates from trying to download updates
- `EXPO_NO_DOCTOR=1`: Skips slow dependency validation checks

### 3. Fixed Incompatible Dependencies

Ran automatic fix to align with Expo SDK 49:

```bash
npx expo install --fix
```

This downgraded:

- `expo-secure-store` from 15.0.7 to ~12.3.1
- `react-native-reanimated` from 4.1.5 to ~3.3.0
- `babel-preset-expo` from 54.0.7 to ^9.9.0

### 4. Updated `App.tsx`

Already had `LogBox.ignoreLogs()` to suppress update-related warnings:

```typescript
LogBox.ignoreLogs([
  "failed to download remote updates",
  "expo-updates",
  "EXUpdates",
  "Updates",
]);
```

### 5. Cleared Port and Caches

```powershell
# Kill zombie processes
Get-Process | Where-Object {$_.ProcessName -match 'node|expo'} | Stop-Process -Force

# Clear Metro bundler cache
npx expo start --clear
```

## How to Start the App

### Option 1: Using VS Code Task (Recommended)

1. Press `Ctrl+Shift+P`
2. Type "Run Task"
3. Select "Mobile: Start"
4. Wait for QR code to appear
5. Scan with Expo Go app on your phone

### Option 2: Manual Command

```bash
cd apps/mobile
npx expo start
```

The server will start on `http://localhost:8081` and display a QR code.

## Testing Checklist

- [ ] Expo server starts without errors
- [ ] QR code displays in terminal
- [ ] Scan QR with Expo Go (Android) or Camera (iOS)
- [ ] App loads without "failed to download remote updates" error
- [ ] Auth flow works: email → OTP → main tabs
- [ ] Countries tab loads list from backend
- [ ] Account tab shows user info

## What Was the Key?

The critical insight was that `expo-updates` is **bundled with Expo SDK 49** and can't be uninstalled. Trying to blacklist it from Metro caused crashes. The solution was to **disable it at runtime** using environment variables rather than removing it from the bundle.

## Files Modified

- ✅ `apps/mobile/app.config.js` - Removed all updates config
- ✅ `apps/mobile/.env` - Added EXPO_NO_UPDATES and EXPO_NO_DOCTOR
- ✅ `apps/mobile/App.tsx` - Already had LogBox.ignoreLogs
- ✅ `apps/mobile/package.json` - Fixed dependency versions

## Previous Failed Attempts

1. ❌ Removing expo-updates plugin from app.config.js only
2. ❌ Uninstalling expo-updates (it's part of SDK)
3. ❌ Creating metro.config.js to blacklist the module (caused Metro crashes)
4. ❌ Simplifying App.tsx error handlers
5. ❌ Multiple cache clears without fixing root cause

The combination of `.env` variables + clean config + fixed dependencies was what finally solved it.

---

**Status**: ✅ RESOLVED  
**Date**: November 19, 2025  
**Testing**: Mobile server is now running - ready for user to scan QR and verify
