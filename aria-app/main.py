import os
from website import create_app
import logging

logger = logging.getLogger(__name__)

app0 = create_app()

if __name__ == '__main__': #only if main.py is run
    if os.environ.get("SEED_DB") == "true":
        logger.info("SEED_DB is set to true. Sourcing seed.py...")
        from seed import seed_database
        seed_database()
        logger.info("Seeding complete.")
        
    port = int(os.environ.get("PORT", 5000))
    app0.run(host='0.0.0.0', port=port, debug=app0.config['DEBUG'])    # Expose app for Docker networking
