#!/usr/bin/python
from datetime import datetime

import os
import time
import subprocess
import socket
import string
import ConfigParser
import statsd

config = ConfigParser.ConfigParser()
config.readfp(open('/home/pi/s2g/s2g.conf'))

usestatsd=config.get('CARBON','STATS')

if "true" in usestatsd:  
	stats = statsd.Connection.set_defaults(host='[GRAPHITEHOST]')
	timer = statsd.Timer('smoke2graphite')
	timer2 = statsd.Timer('smoke2graphite')
	gauge = statsd.Gauge('smoke2graphite')

def get_filepaths(directory):
    """
    This function will generate the file names in a directory 
    tree by walking the tree either top-down or bottom-up. For each 
    directory in the tree rooted at directory top (including top itself), 
    it yields a 3-tuple (dirpath, dirnames, filenames).
    """

    if "true" in usestatsd:
    	timer2.start() #timer for function
    
    filecounter=0
    file_paths = []  # List which will store all of the full filepaths.

    # Walk the tree.
    for root, directories, files in os.walk(directory):
        for filename in files:
	    filecounter+=1
            # Join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)  # Add it to the list.

    if "true" in usestatsd:
    	timer2.stop('get_filespaths') #end timer
	gauge.send('files', filecounter)
    
    print 'Files processed: %i' % filecounter
    return file_paths  # Self-explanatory.
#------------------------------------------------------

if "true" in usestatsd:
	timer.start()

start_time = datetime.now()
print('Started: {}'.format(start_time))


#load stuff from configs
CARBONHOST=config.get('CARBON','CARBONHOST')
CARBONPORT=int(config.get('CARBON','CARBONPORT'))
CARBONPREFIX=config.get('CARBON','CARBONPREFIX')

print "%s:%s" %(CARBONHOST,CARBONPORT)

#get files and directories
rrds = []
rrds = get_filepaths(config.get('Smokeping','SMOKEPINGDATA'))
MASTER = config.get('Smokeping','SMOKEMASTER') 
count=0
timestamp=0
smokestr = []
smokedata = []
for f in rrds:
	if f.endswith(".rrd"):
		host = f.split('/')
		linesize=len(host)-1
		label = host[linesize].split('~')
		#check to se if the result came from the master
		if len(label) == 1:
			HOST=MASTER
		else:
			HOST=label[1].split('.')
			HOST=HOST[0]

		#get last update from rrd file
		response=subprocess.Popen(['rrdtool', 'lastupdate',f], stdout=subprocess.PIPE).communicate()[0]
		results = response.split('\n')
	
		smokestr = results[0].split(' ')
		smokedata = results[2].split(' ')		

		count=0 
		message=""
		timestamp=0
		for str in smokestr:
			if "uptime" in str:
				xtimestamp=smokedata[0][:-1]
				timestamp=xtimestamp.strip(":")
				#message+= "uptime " + timestamp 
				count+=1
				continue
			if "median" in str:
				count+=1
				continue
			elif len(str)<1:
				count+=1
				continue
			else:
				message+= str 
				if "-" in smokedata[count]:
					message+=" %s" %(float(smokedata[count]))
				elif "U" in smokedata[count]:
					message+=" 0"
				else:
					message+=" %s" %(smokedata[count])
				
				#prepare for insertion, grab master from config
				menu = label[0].split('.')
				payload="%s.%s.%s.%s %s\n" % (CARBONPREFIX,HOST,menu[0],message.lstrip(),timestamp)
				
				#write to graphite
				#print 'sending message: %s' % payload
				sock = socket.socket()
				sock.connect((CARBONHOST, CARBONPORT))
				sock.sendall(payload)
				sock.close()
			message=""
			count+=1


end_time = datetime.now()
print('Ended: {}'.format(end_time))

if "true" in usestatsd:
	timer.stop('main_loop')

