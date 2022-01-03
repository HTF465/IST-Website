import os

from portal import app as application

if __name__ == '__main__':
    application.run(
        host='192.168.1.31',
        port=int(os.environ.get('PORT', 5000)),
        debug=True,
        ssl_context=('/home/gene/server.crt', '/home/gene/server.key'),
    )
