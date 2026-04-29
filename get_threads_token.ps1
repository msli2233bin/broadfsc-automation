# Threads OAuth Token Generator
# Run this script and follow the instructions

$APP_ID = "1479983126925807"
$APP_SECRET = "9857adbca8c910959a78e14d813c0e53"
$REDIRECT_URI = "https://www.broadfsc.com/"
$SCOPE = "threads_basic,threads_content_publish"

Write-Host "=== Threads Access Token Generator ===" -ForegroundColor Green
Write-Host ""
Write-Host "Step 1: Open this URL in your browser (already logged in as msli637):" -ForegroundColor Yellow
Write-Host ""
Write-Host "https://www.threads.net/oauth/authorize?client_id=$APP_ID&redirect_uri=$([Uri]::EscapeDataString($REDIRECT_URI))&scope=$SCOPE&response_type=code" -ForegroundColor Cyan
Write-Host ""
Write-Host "Step 2: Authorize the app, then copy the 'code' parameter from the redirect URL" -ForegroundColor Yellow
Write-Host ""

$AUTH_CODE = Read-Host "Paste the authorization code here"

if (-not $AUTH_CODE) {
    Write-Host "No code provided. Exiting." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Exchanging code for access token..." -ForegroundColor Yellow

# Exchange code for short-lived token
$TOKEN_URL = "https://graph.threads.net/oauth/access_token"
$BODY = @{
    client_id = $APP_ID
    client_secret = $APP_SECRET
    grant_type = "authorization_code"
    redirect_uri = $REDIRECT_URI
    code = $AUTH_CODE
}

try {
    $RESPONSE = Invoke-RestMethod -Uri $TOKEN_URL -Method POST -Body $BODY
    $SHORT_TOKEN = $RESPONSE.access_token
    
    Write-Host ""
    Write-Host "Short-lived token received!" -ForegroundColor Green
    Write-Host "Token: $($SHORT_TOKEN.Substring(0, 20))..." -ForegroundColor Gray
    
    # Exchange for long-lived token
    Write-Host ""
    Write-Host "Exchanging for long-lived token (60 days)..." -ForegroundColor Yellow
    
    $LONG_URL = "https://graph.threads.net/v1.0/access_token"
    $LONG_PARAMS = @{
        grant_type = "th_exchange_token"
        client_secret = $APP_SECRET
        access_token = $SHORT_TOKEN
    }
    
    $LONG_RESPONSE = Invoke-RestMethod -Uri $LONG_URL -Method GET -Body $LONG_PARAMS
    $LONG_TOKEN = $LONG_RESPONSE.access_token
    $EXPIRES_IN = $LONG_RESPONSE.expires_in
    
    Write-Host ""
    Write-Host "=== SUCCESS! ===" -ForegroundColor Green
    Write-Host "Long-lived Access Token:" -ForegroundColor Yellow
    Write-Host $LONG_TOKEN -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Expires in: $EXPIRES_IN seconds (~$([math]::Round($EXPIRES_IN/86400)) days)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "User ID: 35426966120283926" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Add these to your .env file:" -ForegroundColor Yellow
    Write-Host "THREADS_ACCESS_TOKEN=$LONG_TOKEN" -ForegroundColor Cyan
    Write-Host "THREADS_USER_ID=35426966120283926" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
}
