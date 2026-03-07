from website import create_app

app0 = create_app()

if __name__ == '__main__': #only if main.py is run
    app0.run(host='0.0.0.0', port=5000, debug=True)    # Expose app for Docker networking
