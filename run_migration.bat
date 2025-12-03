@echo off
cd /d "%~dp0"
echo Running migration...
.venv\Scripts\python.exe migrate_sync.py > migration_output.txt 2>&1
echo Done. Check migration_output.txt for results.
type migration_output.txt
pause

