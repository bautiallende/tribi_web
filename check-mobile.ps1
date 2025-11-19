Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TRIBI MOBILE - STATUS CHECK" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Expo server is running
Write-Host "Checking Expo server..." -NoNewline
$expoRunning = Test-NetConnection -ComputerName localhost -Port 8081 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($expoRunning.TcpTestSucceeded) {
    Write-Host " ✅ RUNNING" -ForegroundColor Green
    Write-Host "  Port: 8081" -ForegroundColor Gray
} else {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    Write-Host "  Run: npm run start in apps/mobile/" -ForegroundColor Yellow
}

Write-Host ""

# Check if backend is running
Write-Host "Checking Backend API..." -NoNewline
$backendRunning = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if ($backendRunning.TcpTestSucceeded) {
    Write-Host " ✅ RUNNING" -ForegroundColor Green
    Write-Host "  Port: 8000" -ForegroundColor Gray
} else {
    Write-Host " ❌ NOT RUNNING" -ForegroundColor Red
    Write-Host "  Start backend to test full mobile auth flow" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  HOW TO TEST MOBILE APP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Expo Go app on your phone" -ForegroundColor White
Write-Host "   - Android: Download from Google Play" -ForegroundColor Gray
Write-Host "   - iOS: Download from App Store" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Look for the QR code in the terminal" -ForegroundColor White
Write-Host "   - It should be displayed by the Mobile: Start task" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Scan the QR code" -ForegroundColor White
Write-Host "   - Android: Use Expo Go app scanner" -ForegroundColor Gray
Write-Host "   - iOS: Use Camera app" -ForegroundColor Gray
Write-Host ""
Write-Host "4. App should load WITHOUT the update error" -ForegroundColor Green
Write-Host "   ✅ No 'failed to download remote updates'" -ForegroundColor Green
Write-Host "   ✅ Should see auth screen (email input)" -ForegroundColor Green
Write-Host ""
Write-Host "5. Test the auth flow:" -ForegroundColor White
Write-Host "   - Enter your email" -ForegroundColor Gray
Write-Host "   - Receive OTP (check terminal)" -ForegroundColor Gray
Write-Host "   - Enter code" -ForegroundColor Gray
Write-Host "   - Should see Countries and Account tabs" -ForegroundColor Gray
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SOLUTION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "The expo-updates error was fixed by:" -ForegroundColor White
Write-Host "  1. ✅ Removed expo-updates config from app.config.js" -ForegroundColor Gray
Write-Host "  2. ✅ Added EXPO_NO_UPDATES=1 to .env" -ForegroundColor Gray
Write-Host "  3. ✅ Fixed incompatible dependencies" -ForegroundColor Gray
Write-Host "  4. ✅ Cleared Metro cache and zombie processes" -ForegroundColor Gray
Write-Host ""
Write-Host "See MOBILE_UPDATE_FIX.md for full details" -ForegroundColor Cyan
Write-Host ""
