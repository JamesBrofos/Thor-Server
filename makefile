# Extract the local area network IP address.
ip_addr = $(shell ifconfig wlp2s0 | grep "inet addr" | cut -d ':' -f 2 | cut -d ' ' -f 1)
timeout=1000
all:
	gunicorn -t $(timeout) -w 4 -b 127.0.0.1:5000 app:app

lan:
	echo $(ip_addr)
	gunicorn -t $(timeout) -w 4 -b $(ip_addr):5000 app:app

dev:
	FLASK_APP=app.py FLASK_DEBUG=1 flask run
