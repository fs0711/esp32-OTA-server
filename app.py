
from esp32OTA import app

def _run():
    """ Imports the app and runs it. """
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    _run()