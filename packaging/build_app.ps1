param(
    [string]$AppName = "peguidenew",
    [switch]$OneFile,
    [switch]$OneDir
)

Set-StrictMode -Version Latest

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $here

# Timestamped build dir
$timestamp = (Get-Date -Format "yyyyMMdd_HHmmss")
$build_dir = Join-Path $here "build\$($AppName)_$timestamp"
Write-Host "Creating build directory: $build_dir"
New-Item -ItemType Directory -Force -Path $build_dir | Out-Null

# Files and folders to copy
$itemsToCopy = @(
    "main.py",
    "main_v3_final.py",
    "main_v3_finalfix.py",
    "model.py",
    "model.tflite",
    "visualization.py",
    "gui_manager_v2.py",
    "gui_manager.py",
    "image_loader.py",
    "generate_audio.py",
    "generate_audio_v2.py",
    "feedback_system.py",
    "instructions.py",
    "pose_verifier.py",
    "generate_estimates.py",
    "evaluate_model.py",
    "evaluate_results",
    "imagedatabase",
    "audio_assets",
    "model_estimates",
    "evaluation_results"
)

foreach ($item in $itemsToCopy) {
    $src = Join-Path $here "..\$item" -Resolve
    if (Test-Path $src) {
        Write-Host "Copying $item to build directory..."
        Copy-Item -Recurse -Force -Path $src -Destination $build_dir
    } else {
        Write-Host "Warning: $item not found, skipping."
    }
}

# Copy launcher
Copy-Item -Force -Path (Join-Path $here 'run_app.py') -Destination $build_dir

# Optional: create a requirements.txt for user's reference
$requirements = @(
    'numpy',
    'opencv-python',
    'tensorflow',
    'scikit-learn',
    'pygame',
    'gTTS',
    'matplotlib',
    'seaborn'
)
$requirements | Out-File -FilePath (Join-Path $build_dir 'requirements.txt') -Encoding utf8

# Check PyInstaller availability
try {
    pyinstaller --version | Out-Null
} catch {
    Write-Host "PyInstaller not found. Installing it in the system environment..."
    python -m pip install --upgrade pip
    python -m pip install pyinstaller
}

# Build with PyInstaller
Push-Location $build_dir

$entry = 'run_app.py'
$addDataArgs = @()

# Add data for folders (PyInstaller expects source;dest separated by ; on Windows)
$extras = @('imagedatabase','model.tflite','audio_assets','model_estimates','evaluation_results')
foreach ($e in $extras) {
    if (Test-Path $e) {
        $addDataArgs += "--add-data `"$e;$e`""
    }
}

if ($OneFile) {
    $pyiMode = '--onefile'
} else {
    # default to onedir
    $pyiMode = '--onedir'
}

$cmd = "pyinstaller --noconfirm $pyiMode --windowed $($addDataArgs -join ' ') $entry"
Write-Host "Running: $cmd"
Invoke-Expression $cmd

Pop-Location

Write-Host "Build copy saved at: $build_dir"
Write-Host "If build succeeded, built artifacts are in $build_dir\dist\"

Pop-Location
