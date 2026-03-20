python -m pytest tests/ -v --tb=short 2>&1 && python -m PyInstaller camunda-monitor.spec --distpath dist --workpath build --noconfirm 2>&1 
