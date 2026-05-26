#!/bin/bash
cd /app/legiongasper_framework_0813
pip install -r requirements.txt -q
python3 -c "from ui.app import run_app; run_app(host='0.0.0.0', port=8080)"
