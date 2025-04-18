from app import create_app, socketio

# Create application instance
application = create_app()

# For render and other WSGI servers
app = application

if __name__ == "__main__":
    socketio.run(application, host='0.0.0.0', port=8000) 
    