
#!/bin/bash
# Startup script for the App Build Deploy System (Linux/Mac)

echo "Starting App Build Deploy System..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers if needed
echo "Installing Playwright browsers..."
playwright install

# Initialize database
echo "Initializing database..."
python database/database.py

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo
    echo "WARNING: .env file not found!"
    echo "Please copy .env.template to .env and configure your settings."
    echo
    read -p "Press enter to continue..."
    exit 1
fi

# Start services
echo
echo "Starting services..."
echo

# Start evaluation API in background
echo "Starting evaluation API on port 5001..."
python evaluation_system/evaluation_api.py &
EVAL_PID=$!

# Wait a moment for evaluation API to start
sleep 3

# Start student API
echo "Starting student API on port 5000..."
echo
echo "System is ready!"
echo
echo "Student API: http://localhost:5000"
echo "Evaluation API: http://localhost:5001"
echo "Health check: http://localhost:5000/health"
echo

# Function to cleanup on exit
cleanup() {
    echo
    echo "Shutting down..."
    kill $EVAL_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start student API (foreground)
python student_api/app.py

# Cleanup
cleanup