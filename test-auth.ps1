# Test authentication flow
Write-Host "========================================"
Write-Host "Testing Tribi Authentication Flow"
Write-Host "========================================"
Write-Host ""

$email = "admin@tribi.com"
$baseUrl = "http://localhost:8000"

# Step 1: Request OTP code
Write-Host "Step 1: Requesting OTP code for $email..."
try {
    $body = @{ email = $email } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/request-code" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
    Write-Host "SUCCESS: OTP code requested"
    Write-Host "Check the backend terminal for the OTP code"
} catch {
    Write-Host "ERROR: Failed to request OTP: $_"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "Check backend terminal for:"
Write-Host "  EMAIL TO: $email"
Write-Host "  BODY: Your login code is: XXXXXX"
Write-Host "========================================"
Write-Host ""

$code = Read-Host "Enter the 6-digit OTP code"

# Step 2: Verify OTP code
Write-Host ""
Write-Host "Step 2: Verifying OTP code..."
try {
    $session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
    $body = @{ email = $email; code = $code } | ConvertTo-Json
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/verify" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body -SessionVariable session
    Write-Host "SUCCESS: OTP verified"
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Token received"
} catch {
    Write-Host "ERROR: Failed to verify OTP: $_"
    exit 1
}

# Step 3: Test /auth/me endpoint
Write-Host ""
Write-Host "Step 3: Testing /auth/me endpoint..."
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/auth/me" -Method GET -WebSession $session
    $user = $response.Content | ConvertFrom-Json
    Write-Host "SUCCESS: Authenticated as $($user.email)"
} catch {
    Write-Host "ERROR: Failed to get user info"
    Write-Host "This means cookies are not working"
    exit 1
}

# Step 4: Test admin access
Write-Host ""
Write-Host "Step 4: Testing admin access..."
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/admin/countries?page=1&page_size=5" -Method GET -WebSession $session
    Write-Host "SUCCESS: Admin access confirmed"
    $countries = $response.Content | ConvertFrom-Json
    Write-Host "Found $($countries.total) countries"
} catch {
    Write-Host "ERROR: Admin access failed"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "All tests passed!"
Write-Host "========================================"
Write-Host ""
Write-Host "Now test in browser:"
Write-Host "1. Open http://localhost:3000/auth"
Write-Host "2. Login with $email"
Write-Host "3. Enter OTP from backend logs"
Write-Host "4. Go to http://localhost:3000/admin"
