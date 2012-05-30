build:
	echo "Nothing to build. Only install."

install:
	pip install -r requirements.txt
	mkdir -p /var/lib/selfspy
	cp *.py /var/lib/selfspy
	mkdir -p ~/.selfspy
	ln -s /var/lib/selfspy/selfspy.py /usr/bin/selfspy
	ln -s /var/lib/selfspy/selfstats.py /usr/bin/selfstats
