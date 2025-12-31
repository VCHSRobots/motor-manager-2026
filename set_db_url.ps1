# PowerShell script to set DATABASE_URL
param(
    [string]$DatabaseName = "dynamometer_db",
    [string]$HostName = "localhost",
    [string]$Port = "5432",
    [string]$Username = "postgres"
)

# Prompt for password securely
$Password = Read-Host -Prompt "Enter PostgreSQL password for user '$Username'" -AsSecureString
$PasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password))

# Construct DATABASE_URL
$DATABASE_URL = "postgresql://$Username`:$PasswordPlain@$HostName`:$Port/$DatabaseName"

# Set environment variable
$env:DATABASE_URL = $DATABASE_URL

Write-Host "DATABASE_URL has been set to: postgresql://$Username`:***@$HostName`:$Port/$DatabaseName"
Write-Host "You can now run: python scripts/setup_db.py"