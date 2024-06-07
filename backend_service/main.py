from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
import uvicorn
from backend_service.helper_functions import get_port, setup_logger


def main():
    """
    Entry point for the application.
    """
    logger = setup_logger('backend_service_logger')
    port = get_port()

    logger.info("Starting backend service..")
    uvicorn.run("backend_service.app:app", port=port, host="0.0.0.0", workers=1, reload=True)

if __name__ == "__main__":
    main()