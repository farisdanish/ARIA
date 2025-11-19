from website import create_app

app0 = create_app()

if __name__ == '__main__': #only if main.py is run
    app0.run(debug=True)    #the web server will run #debug will be off/false after production