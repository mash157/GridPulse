@echo off
echo ============================================
echo  GridPulse - Smart Energy Grid Monitoring
echo ============================================
echo.

echo [Step 1] Generating dataset...
python data_generation/generate_dataset.py --records 150000

echo.
echo [Step 2] Running Bronze pipeline...
python pipeline/01_bronze_batch_ingest.py

echo.
echo [Step 3] Running Silver pipeline...
python pipeline/03_silver_transform.py

echo.
echo [Step 4] Running Gold aggregation...
python pipeline/04_gold_aggregate.py

echo.
echo [Step 5] Starting FastAPI backend...
echo Open a new terminal and run:
echo   uvicorn backend.api.main:app --reload --port 8000
echo.

echo [Step 6] Starting streaming generator...
echo Open a new terminal and run:
echo   python data_generation/generate_stream.py
echo.

echo [Step 7] Starting Next.js frontend...
echo Open a new terminal and run:
echo   cd frontend ^&^& npm install ^&^& npm run dev
echo.

echo ============================================
echo  All steps prepared!
echo ============================================
