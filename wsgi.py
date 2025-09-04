from app import app
import newrelic

if __name__ == "__main__":
    app.run()

newrelic_ini = 'newrelic.ini'

try:
    import newrelic.agent
except:
    print("newrelic not found")
    application = app
else:
    print("newrelic APM running")
    newrelic.agent.initialize(newrelic_ini, 'staging')
    @newrelic.agent.wsgi_application()
    def application(environ, start_response):
        _application = app
        return _application(environ, start_response)