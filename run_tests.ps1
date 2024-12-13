#
# Run all Python unit tests
#

# Change the cwd to where this script lives
Push-Location $(Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

# Test for python
$PYTHON = Get-Command -ErrorAction SilentlyContinue "python"
If (-not $PYTHON) {
    Write-Host "Cannot find Python interpreter"
    Pop-Location
    Exit 1
} Else {
    $py_ver = & $PYTHON.Source "-V"
    Write-Host "Using $($py_ver): $($PYTHON.Source)"
}

# Check for the coverage package
$null = & $PYTHON.Source -m coverage 2>$null
If ($LASTEXITCODE -eq 0) {
    # Run tests with code coverage
    Write-Host "To see code coverage, run: $($PYTHON.Name) -m coverage report"
    & $PYTHON.Source -m coverage run -m unittest discover -v -p 'test_*.py'
} Else {
    # Run tests w/o code coverage
    & $PYTHON.Source -m unittest discover -v -p 'test_*.py'
}

# Restore original cwd
Pop-Location
