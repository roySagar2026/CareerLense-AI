# Prints a random URL-safe secret suitable for JWT_SECRET (works on Windows PowerShell 5.1 and pwsh 7).
$bytes = New-Object 'System.Byte[]' 48
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$rng.Dispose()
[Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
