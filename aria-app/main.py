import os
from website import create_app

app0 = create_app()

if __name__ == '__main__': #only if main.py is run
    if os.environ.get("SEED_DB") == "true":
        print("SEED_DB is set to true. Sourcing seed.py...")
        from seed import seed_database
        seed_database()
        print("Seeding complete.")
        
    port = int(os.environ.get("PORT", 5000))
    app0.run(host='0.0.0.0', port=port, debug=True)    # Expose app for Docker networking
