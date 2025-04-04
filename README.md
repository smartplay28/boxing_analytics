# Boxing Analytics

A real-time boxing analytics platform that uses computer vision to detect and analyze boxing punches and combinations.

## Features

- Real-time punch detection and classification
- Fighter profile management
- Session tracking and analysis
- Combination detection
- Speed and power metrics
- Web dashboard with real-time updates

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy (SQLite in development, PostgreSQL in production)
- **Real-time Communication**: Socket.IO
- **Computer Vision**: OpenCV, YOLOv8 (pose detection)
- **Frontend**: HTML, CSS, JavaScript, Chart.js

## Setup Instructions

### Prerequisites

- Python 3.8+
- OpenCV
- PyTorch
- Node.js (for frontend development, optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/boxing_analytics.git
cd boxing_analytics
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run database migrations:
```bash
python -c "from app import create_app; from app.models.models import db; app = create_app(); with app.app_context(): db.create_all()"
```

5. Start the development server:
```bash
python main.py
```

6. Open your browser and navigate to `http://localhost:5000`

### Configuration

Configuration options can be set in `app/config.py` or via environment variables:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Flask secret key
- `VIDEO_STORAGE_PATH`: Path to store recorded videos
- `CAMERA_IDS`: Comma-separated list of camera IDs to use

## Usage

1. Add fighters through the API or web interface
2. Start a new training session
3. Monitor real-time stats and analytics on the dashboard
4. End the session to view the full session report

## Development

### Project Structure

```
boxing_analytics/
├── app/
│   ├── models/         # Database models
│   ├── routes/         # API endpoints
│   ├── services/       # Business logic and services
│   ├── socket/         # Socket.IO handlers
│   ├── static/         # Frontend assets
│   ├── templates/      # HTML templates
│   ├── utils/          # Utility functions
│   ├── __init__.py     # Application factory
│   └── config.py       # Application configuration
├── main.py             # Application entry point
└── requirements.txt    # Python dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.