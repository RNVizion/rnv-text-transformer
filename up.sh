pip install -r requirements.txt -r requirements-dev.txt
export QT_QPA_PLATFORM=offscreen
pytest tests/test_snapshots.py --snapshot-update
