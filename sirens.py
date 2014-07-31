from sys import argv, exit
from httplib2 import *
import time
import json
import os
import threading
import codecs

JsonUrl = r'http://www.oref.org.il/WarningMessages/alerts.json'

class Alerter:
	def __init__(self, json_url):
		self.__json_url__ = json_url
		self.__http__ = Http()
	
	def __alerter_thread__(self):
		prev_id = 0
		prev_alerts = []
		while (self.__run_thread__):
			try:
				alert_json = json.loads(HttpHelper.http_get(self.__http__, self.__json_url__, 'utf16'))
				alerts, cur_id = self.get_alerts(alert_json, prev_id)
				alerts.sort()
				if alerts != prev_alerts:
					try:
						self.__handler__.handle(alerts)
					except Exception as e:
						print 'Error in handler: %s' % e.message
					prev_id = cur_id
					prev_alerts = alerts
			except Exception, e:
				print "Error acquiring/parsing json: %s" % e.message
			time.sleep(10)		

	def start(self, handler):
		self.__handler__ = handler
		self.__run_thread__ = True
		self.__thread__ = threading.Thread(target=self.__alerter_thread__)
		self.__thread__.start()
	
	def stop(self):
		self.__run_thread__ = False

	@staticmethod
	def get_alerts(alert_json, last_id):
		keys = alert_json.keys()
		if u'id' not in keys or u'title' not in keys or u'data' not in keys:
			raise Exception("Required fields not found in json")
		#check if this alert is identical to the previous
		if last_id == alert_json[u'id']: return [], last_id
		return alert_json[u'data'], alert_json[u'id']
	
class HttpHelper:
	@staticmethod
	def http_get(http, url, encoding=None):
		res, content = http.request(url)
		if not res.has_key('status'):
			raise Exception("Status code missing from response")
		if res['status'] != '200':
			raise Exception("Failed to retrieve page, status code: %s" % res['status'])
		if encoding:
			return content.decode(encoding)
		else:
			return content

class AlertHandler:
	def __init__(self, file_path, print_to_screen, git_commit_and_push = False):
		self.__file_path__ = file_path
		self.__print_to_screen__ = print_to_screen
		self.__git_commit_and_push__ = git_commit_and_push

	def handle(self, alerts):
		if len(alerts) == 0:
			self.print_message(u'אין אזעקות\n')
		else:
			self.print_message(u'אזעקות ב: ' + u', '.join(alerts) + u'\n')

	def print_message(self, message):
		cur_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime())
		formatted_msg = "%s - %s" % (cur_time, message)
		if self.__print_to_screen__: print formatted_msg
		if self.__file_path__ != None:
			with codecs.open(self.__file_path__, 'a', 'utf8') as f:
				f.write(formatted_msg)
			if self.__git_commit_and_push__:
				file_dir = os.path.split(self.__file_path__)
				commit_cmd = 'git commit -m "Updated siren file" %s' % os.path.join(self.__file_path__)
				if (0 != os.system("%s" % commit_cmd)): raise Exception("Failed to commit")
				push_cmd = 'git push'
				if (0 != os.system("%s" % push_cmd)): raise Exception("Failed to push")

def main(argv):
	if len(argv) not in (1, 2):
		print 'Usage: %s [output_file]' % os.path.split(argv[0])[1]
		return -1

	file_path = None
	if len(argv) == 2: file_path = argv[1]

	handler = AlertHandler(file_path, False, True)
	alerter = Alerter(JsonUrl)
	
	alerter.start(handler)
	x = raw_input("click enter to exit")
	alerter.stop()


if __name__ == "__main__":
	exit(main(argv))