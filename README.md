#smoke2graphite

Configure s2g.conf to your liking then either run by hand or via cron, e.g.
*/2 * * * * /usr/bin/python /home/pi/s2g/s2g.py >>/home/pi/s2g/s2g.log 2>&1

Script uses file names to determine hosts tests were run from and assumes a master/slave setup.

