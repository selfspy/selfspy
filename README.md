### What is this?
Selfspy is a daemon for Unix/X11, (thanks to @ljos!) Mac OS X and (thanks to @Foxboron) Windows, that continuously monitors and stores what you are doing on your computer. This way, you can get all sorts of nifty statistics and reminders on what you have been up to. It is inspired by the [Quantified Self](http://en.wikipedia.org/wiki/Quantified_Self)-movement and [Stephen Wolfram's personal key logging](http://blog.stephenwolfram.com/2012/03/the-personal-analytics-of-my-life/).

See Example Statistics, below, for some of the fabulous things you can do with this data.

### Windows

Due to Windows libs needing a external compiler to compile libs, some libs won't compile on all computers.   
These are the sinners*:   
`pyHook==1.5.1`   
`pyCrypto==2.5 `   
They are added too the windows-requirements.txt, but IF you fail to build these libs, here are the precompiled binaries. pyWin32 is needed for some library dependency, pip can't install pyWin32, so please use the binary below.      
pyHook: http://sourceforge.net/projects/pyhook/files/pyhook/   
pyCrytpo: http://www.voidspace.org.uk/python/modules.shtml#pycrypto   
pyWin32: http://sourceforge.net/projects/pywin32/files/pywin32/  
  
*SQLAlchemy does compile without the external compiler, but it uses a clean Python version which might slow things down.  
   
### Installing Selfspy

If you run ArchLinux, here is an AUR package which may be up-to-date:
https://aur.archlinux.org/packages/selfspy-git/

To install manually, either clone the repository from Github (git clone git://github.com/gurgeh/selfspy), or click on the Download link on http://github.com/gurgeh/selfspy/ to get the latest Python source.

Selfspy is only tested with Python 2.7 and has a few dependencies on other Python libraries that need to be satisfied. These are documented in the requirements.txt file. If you are on Linux, you will need subversion installed for pip to install python-xlib. If you are on Mac, you will not need to install python-xlib at all. Python-xlib is currently a tricky package to include in the requirements since it is not on PyPi.
```
pip install svn+https://python-xlib.svn.sourceforge.net/svnroot/python-xlib/tags/xlib_0_15rc1/ # Only do this step on Linux!
python setup.py install
```

You will also need the ``Tkinter`` python libraries. On ubuntu and debian

```
sudo apt-get install python-tk
```

On FreeBSD

```
cd /usr/ports/x11-toolkits/py-tkinter/
sudo make config-recursive && sudo make install clean
```


There is also a simple Makefile. Run `make install` as root/sudo, to install the files in /var/lib/selfspy and also create the symlinks /usr/bin/selfspy and /usr/bin/selfstats.

Report issues here:
https://github.com/gurgeh/selfspy/issues

General discussion here:
http://ost.io/gurgeh/selfspy

#### OS X
In OS X you also need to enable access for assistive devices.
To do that in &lt;10.9 there is a checkbox in `System Preferences > Accessibility`,
in 10.9 you have to add the correct application in
`System Preferences > Privacy > Accessibility`.

### Running Selfspy
You run selfspy with `selfspy`. You should probably start with `selfspy --help` to get to know the command line arguments. As of this writing, it should look like this:

```
usage: selfspy [-h] [-c FILE] [-p PASSWORD] [-d DATA_DIR] [-n]
               [--change-password]

Monitor your computer activities and store them in an encrypted database for
later analysis or disaster recovery.

optional arguments:
  -h, --help            show this help message and exit
  -c FILE, --config FILE
                        Config file with defaults. Command line parameters
                        will override those given in the config file. The
                        config file must start with a "[Defaults]" section,
                        followed by [argument]=[value] on each line.
  -p PASSWORD, --password PASSWORD
                        Encryption password. If you want to keep your database
                        unencrypted, specify -p "" here. If you don't specify
                        a password in the command line arguments or in a
                        config file, a dialog will pop up, asking for the
                        password. The most secure is to not use either command
                        line or config file but instead type it in on startup.
  -d DATA_DIR, --data-dir DATA_DIR
                        Data directory for selfspy, where the database is
                        stored. Remember that Selfspy must have read/write
                        access. Default is ~/.selfspy
  -n, --no-text         Do not store what you type. This will make your
                        database smaller and less sensitive to security
                        breaches. Process name, window titles, window
                        geometry, mouse clicks, number of keys pressed and key
                        timings will still be stored, but not the actual
                        letters. Key timings are stored to enable activity
                        calculation in selfstats. If this switch is used,
                        you will never be asked for password.
  -r, --no-repeat       Do not store special characters as repeated
                        characters.
  --change-password     Change the password used to encrypt the keys columns
                        and exit.
```

Everything you do is stored in a Sqlite database in your DATA_DIR. Things that you type (passwords, for example) are generally too sensitive to leave in plain text, so they are encrypted with the supplied password. Other database columns, like process names and window titles, are not encrypted. This makes it faster and easier to search for them later.

Unless you use the --no-text flag, selfspy will store everything you type in two <a href="http://en.wikipedia.org/wiki/Blowfish_(cipher)">Blowfish</a> encrypted columns in the database.

Normally you would like Selfspy to start automatically when you launch X. How to do this depends on your system, but it will normally mean editing *~/.xinitrc* or *~/.xsession*. If you run KDE, *~/.kde/Autostart*, is a good place to put startup scripts. When run, Selfspy will immediately spawn a daemon and exit.

#### Running on login in OS X
If you want selfspy to start automatically on login you need to copy the [com.github.gurgeh.selfspy.plist](https://raw.githubusercontent.com/gurgeh/selfspy/master/com.github.gurgeh.selfspy.plist)
file to `~/Library/LaunchAgents/`.

### Example Statistics
*"OK, so now all this data will be stored, but what can I use it for?"*

While you can access the Sqlite tables directly or, if you like Python, import `models.py` from the Selfspy directory and use those SqlAlchemy classes, the standard way to query your data is through `selfstats`.

Here are some standard use cases:

*"Damn! The browser just threw away everything I wrote, because I was not logged in."*

`selfstats --back 30 m --showtext`

Show me everything I have written the last 30 minutes. This will ask for my password, in order to decrypt the text.

*"Hmm.. what is my password for Hoolaboola.com?"*

`selfstats -T "Hoolaboola" -P Google-chrome --showtext`

This shows everything I have ever written in Chrome, where the window title contained something with "Hoolaboola". The regular expressions are case insensitive, so I actually did not need the caps. If I have written a lot on Hoolaboola, perhaps I can be more specific in the title query, to only get the login page.

*"I need to remember what I worked on a few days ago, for my time report."*

`selfstats --date 10 --limit 1 d -P emacs --tkeys`

What buffers did I have open in Emacs on the tenth of this month and one day forward? Sort by how many keystrokes I wrote in each. This only works if I have set Emacs to display the current buffer in the window title. In general, try to set your programs (editors, terminals, web apps, ...) to include information on what you are doing in the window title. This will make it easier to search for later. 

On a related but opposite note: if you have the option, remove information like "mails unread" or "unread count" (for example in Gmail and Google Reader) from the window titles, to make it easier to group them in --tactive and --tkeys.

*"Also, when and how much have I used my computer this last week?"*

`selfstats -b 1 w --periods 180`

This will display my active time periods for the last week. A session is considered inactive when I have not clicked or used the keyboard in 180 seconds. Increase that number to get fewer and larger sessions listed.

*"How effective have I been this week?"*

`selfstats -b 1 w --ratios`

This will show ratios informing me about how much I have written per active second and how much I have clicked vs used the keyboard. For me, a lot of clicking means too much browsing or inefficient use of my tools. Track these ratios over time to get a sense of what is normal for you.

*"I remember that I wrote something to her about the IP address of our printer a few months ago. I can't quite remember if it was a chat, a tweet, a mail, a facebook post, or what.. Should I search them separately? No."*

`selfstats --body printer -s --back 40 w`

Show the texts where I have used the word printer in the last 10 weeks. If it turns out that the actual IP adress is not in the same text chunk as when you wrote "printer", you can note the row ID and use --id 
 (or --date and --clock) and --limit to show what else you wrote around that time.

*"What programs do I use the most?"*

`selfstats --pactive`

List all programs I have ever used in order of time active in them.

*"Which questions on the website Stack Overflow did I visit yesterday?"*

`./selfstats -T "Stack Overflow" -P Google-chrome --back 32 h --tactive`

List all window titles that contained "Stack Overflow" the last 32 hours. Sort by time active. I add the sorting, not only because I want them sorted, but because otherwise the listing would show a row for each time I visited that title, instead of grouping them together.

*"How much have I browsed today?"*

`selfstats -P Google-chrome --clock 00:00 --tactive`

This will show all the different pages I visited in the Chrome browser, ordered by for how long I was active.

*"Who needs Qwerty? I am going to make an alternative super-programmer-keymap. I wonder what keys I use the most when I code C++?"*

`selfstats --key-freq -P Emacs -T cpp`

This will list all keys in order of how much I have pressed them in Emacs, while editing a file where the name contained "cpp".

*"While we are at it, which cpp files have I edited the most this month?"*

`selfstats -P Emacs -T cpp --tkeys --date 1`

List all buffers in Emacs that contained "cpp", from the first this month and forward. Sort by how much I typed in them.

Selfstats is a swiss army knife of self knowledge. Experiment with it when you have acquired a few days of data. Remember that if you know SQL or SqlAlchemy, it is easy to construct your own queries against the database to get exactly the information you want, make pretty graphs, etc. There are a few stored properties, like coordinates of a mouse click and window geometry, that you can currently only reach through the database.

### Selfstats Reference

The --help is a beast that right now looks something like this:

```
usage: selfstats [-h] [-c FILE] [-p PASSWORD] [-d DATA_DIR] [-s]
                    [-D DATE [DATE ...]] [-C CLOCK] [-i ID]
                    [-b BACK [BACK ...]] [-l LIMIT [LIMIT ...]] [-m nr]
                    [-T regexp] [-P regexp] [-B regexp] [--ratios] [--clicks]
                    [--key-freqs] [--human-readable] [--active [seconds]] [--periods [seconds]]
                    [--pactive [seconds]] [--tactive [seconds]] [--pkeys]
                    [--tkeys]

Calculate statistics on selfspy data. Per default it will show non-text
information that matches the filter. Adding '-s' means also show text. Adding
any of the summary options will show those summaries over the given filter
instead of the listing. Multiple summary options can be given to print several
summaries over the same filter. If you give arguments that need to access text
/ keystrokes, you will be asked for the decryption password.

optional arguments:
  -h, --help            show this help message and exit
  -c FILE, --config FILE
                        Config file with defaults. Command line parameters
                        will override those given in the config file. Options
                        to selfspy goes in the "[Defaults]" section, followed
                        by [argument]=[value] on each line. Options specific
                        to selfstats should be in the "[Selfstats]" section,
                        though "password" and "data-dir" are still read from
                        "[Defaults]".
  -p PASSWORD, --password PASSWORD
                        Decryption password. Only needed if selfstats needs to
                        access text / keystrokes data. If your database in not
                        encrypted, specify -p="" here. If you don't specify a
                        password in the command line arguments or in a config
                        file, and the statistics you ask for require a
                        password, a dialog will pop up asking for the
                        password. If you give your password on the command
                        line, remember that it will most likely be stored in
                        plain text in your shell history.
  -d DATA_DIR, --data-dir DATA_DIR
                        Data directory for selfspy, where the database is
                        stored. Remember that Selfspy must have read/write
                        access. Default is ~/.selfspy
  -s, --showtext        Also show the text column. This switch is ignored if
                        at least one of the summary options are used. Requires
                        password.
  -D DATE [DATE ...], --date DATE [DATE ...]
                        Which date to start the listing or summarizing from.
                        If only one argument is given (--date 13) it is
                        interpreted as the closest date in the past on that
                        day. If two arguments are given (--date 03 13) it is
                        interpreted as the closest date in the past on that
                        month and that day, in that order. If three arguments
                        are given (--date 2012 03 13) it is interpreted as
                        YYYY MM DD
  -C CLOCK, --clock CLOCK
                        Time to start the listing or summarizing from. Given
                        in 24 hour format as --clock 13:25. If no --date is
                        given, interpret the time as today if that results in
                        sometimes in the past, otherwise as yesterday.
  -i ID, --id ID        Which row ID to start the listing or summarizing from.
                        If --date and/or --clock is given, this option is
                        ignored.
  -b BACK [BACK ...], --back BACK [BACK ...]
                        --back <period> [<unit>] Start the listing or summary
                        this much back in time. Use this as an alternative to
                        --date, --clock and --id. If any of those are given,
                        this option is ignored. <unit> is either "s"
                        (seconds), "m" (minutes), "h" (hours), "d" (days) or
                        "w" (weeks). If no unit is given, it is assumed to be
                        hours.
  -l LIMIT [LIMIT ...], --limit LIMIT [LIMIT ...]
                        --limit <period> [<unit>]. If the start is given in
                        --date/--clock, the limit is a time period given by
                        <unit>. <unit> is either "s" (seconds), "m" (minutes),
                        "h" (hours), "d" (days) or "w" (weeks). If no unit is
                        given, it is assumed to be hours. If the start is
                        given with --id, limit has no unit and means that the
                        maximum row ID is --id + --limit.
  -m nr, --min-keys nr  Only allow entries with at least <nr> keystrokes
  -T regexp, --title regexp
                        Only allow entries where a search for this <regexp> in
                        the window title matches something. All regular expressions
                        are case insensitive.
  -P regexp, --process regexp
                        Only allow entries where a search for this <regexp> in
                        the process matches something.
  -B regexp, --body regexp
                        Only allow entries where a search for this <regexp> in
                        the body matches something. Do not use this filter
                        when summarizing ratios or activity, as it has no
                        effect on mouse clicks. Requires password.
  --clicks              Summarize number of mouse button clicks for all
                        buttons.
  --key-freqs           Summarize a table of absolute and relative number of
                        keystrokes for each used key during the time period.
                        Requires password.
  --human-readable      This modifies the --body entry and honors backspace.
  --active [seconds]    Summarize total time spent active during the period.
                        The optional argument gives how many seconds after
                        each mouse click (including scroll up or down) or
                        keystroke that you are considered active. Default is
                        180.
  --ratios [seconds]    Summarize the ratio between different metrics in the
                        given period. "Clicks" will not include up or down
                        scrolling. The optional argument is the "seconds"
                        cutoff for calculating active use, like --active.
  --periods [seconds]   List active time periods. Optional argument works same
                        as for --active.
  --pactive [seconds]   List processes, sorted by time spent active in them.
                        Optional argument works same as for --active.
  --tactive [seconds]   List window titles, sorted by time spent active in
                        them. Optional argument works same as for --active.
  --pkeys               List processes sorted by number of keystrokes.
  --tkeys               List window titles sorted by number of keystrokes.

See the README file or http://gurgeh.github.com/selfspy for examples.
```

### Email
To monitor that Selfspy works as it should and to continuously get feedback on yourself, it is good to  regularly mail yourself some statistics. I think the easiest way to automate this is using [sendEmail](http://www.debianadmin.com/how-to-sendemail-from-the-command-line-using-a-gmail-account-and-others.html), which can do neat stuff like send through your Gmail account.

For example, put something like this in your weekly [cron](http://clickmojo.com/code/cron-tutorial.html) jobs:
`/(PATH_TO_FILE)/selfstats --back 1 w --ratios 900 --periods 900 | /usr/bin/sendEmail -q -u "Weekly selfstats" <etc..>`
This will give you some interesting feedback on how much and when you have been active this last week and how much you have written vs moused, etc.
