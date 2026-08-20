$env:PYTHONPATH = "E:\files\backend:$env:PYTHONPATH"
$logfile = "$env:TEMP\uvicorn.log"
$process = & nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > $logfile 2>&1 &
Write-Output "Started PID: $($process.Id)"
Start-Sleep -Seconds 3
curl -s http://localhost:8000/health