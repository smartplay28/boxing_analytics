import asyncio
from app import create_app
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

app = create_app()

async def run_app():
    logging.info("Starting development server on http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    asyncio.run(run_app())