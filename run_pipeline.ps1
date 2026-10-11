$hadoopDir = "$PSScriptRoot\hadoop"
$env:HADOOP_HOME = $hadoopDir
$env:Path = "$env:Path;$hadoopDir\bin"
$env:PYTHONPATH = "$PSScriptRoot;$PSScriptRoot\src"

. .\.venv\Scripts\Activate.ps1

Write-Host "Running generation..."
python -m src.fraud_detection.generation.run_generation
if ($LASTEXITCODE -ne 0) { throw "Generation failed" }

Write-Host "Running bronze..."
python -m src.fraud_detection.ingestion.batch_ingest
if ($LASTEXITCODE -ne 0) { throw "Bronze failed" }

Write-Host "Running silver..."
python -m src.fraud_detection.processing.build_silver
if ($LASTEXITCODE -ne 0) { throw "Silver failed" }

Write-Host "Running gold..."
python -m src.fraud_detection.features.build_gold
if ($LASTEXITCODE -ne 0) { throw "Gold failed" }

Write-Host "Running training..."
python -m src.fraud_detection.models.train
if ($LASTEXITCODE -ne 0) { throw "Training failed" }

Write-Host "Running stream consumer..."
python -m src.fraud_detection.streaming.consumer
if ($LASTEXITCODE -ne 0) { throw "Stream consumer failed" }

Write-Host "Running scenario analysis..."
python -m src.fraud_detection.analysis.scenarios
if ($LASTEXITCODE -ne 0) { throw "Scenario analysis failed" }

Write-Host "Pipeline completed successfully."
