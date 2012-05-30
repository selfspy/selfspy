build:
	echo "Nothing to build. Only install. Destination is: " $(DESTDIR)

install:
	mkdir -p $(DESTDIR)/var/lib/selfspy
	cp *.py $(DESTDIR)/var/lib/selfspy
	mkdir -p ~/.selfspy
	ln -s $(DESTDIR)/var/lib/selfspy/selfspy.py $(DESTDIR)/usr/bin/selfspy
	ln -s $(DESTDIR)/var/lib/selfspy/selfstats.py $(DESTDIR)/usr/bin/selfstats
