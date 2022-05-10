import tweepy
import re
import os
import shutil
import json
import time
import yt_dlp
from appval import *
import sqlite3 as sl
con = sl.connect('sqldb/music.db')

class MyCustomPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        self.to_screen('Doing stuff')
        return [], info


def my_posthook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')


ydl_opts = {
        'format': 'bestaudio/best',
        "postprocessors": 
        [{"key" : "FFmpegExtractAudio"}, {"key" : "FFmpegMetadata"}],
        'postprocessor_hooks': [my_posthook]
}



auth = tweepy.OAuth1UserHandler(
	consumer_key, consumer_secret, access_token, access_token_secret
	)

api = tweepy.API(auth)


def sql_prepare():
        with con:
             con.execute("""
                CREATE TABLE IF NOT EXISTS DOWNLOAD (
                        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                        link TEXT,
                        folder TEXT,
                        who INTEGER,
                        time INTEGER,
                        execute INTEGER
                        );
                """)

        with con:
                con.execute(""" CREATE UNIQUE INDEX IF NOT EXISTS DOWNLOAD_link on DOWNLOAD ( link ); """)

        with con:
             con.execute("""
                CREATE TABLE IF NOT EXISTS TIMESTAMP (
                        id INTEGER NOT NULL PRIMARY KEY,
                        timestamp_current INTEGER );
                """)

        with con:
                con.execute(""" INSERT OR IGNORE INTO TIMESTAMP (id, timestamp_current) values (0, 0); """)

def sql_insert(link, folder, who, time, execute):
        sql = 'INSERT OR IGNORE INTO DOWNLOAD (link, folder, who, time, execute) values(?, ?, ?, ?, ?)'
        data = [
        (link, folder, who, time, execute)
        ]
        with con:
            con.executemany(sql, data)

def update_timestamp(timestamp_current):
        sql = 'UPDATE TIMESTAMP SET timestamp_current=? WHERE id==0'
        with con:
                con.execute(sql, (timestamp_current,)) 

def update_download(id):
	sql = 'UPDATE DOWNLOAD SET execute=1 WHERE id=?'
	with con:
		con.execute(sql, (id,))

def get_timestamp():
	with con:
		data = con.execute("SELECT timestamp_current FROM TIMESTAMP WHERE id=0")
		for row in data:
			r= row[0]
			return r

def sql_delete_row(row):
	sql = 'DELETE FROM DOWNLOAD WHERE id==?'
	with con:
		con.execute(sql, (row,))

def test1():
	with con:
		data = con.execute("SELECT * FROM DOWNLOAD WHERE execute == 0")
		for row in data:
			print(row)

def test3():
        with con:
                data = con.execute("SELECT * FROM TIMESTAMP")
                for row in data:
                        print(row)

def get_fromtwitter():
	print("step A")
	r = get_timestamp()
	dm = api.get_direct_messages(count=5)
	for dms in reversed(dm):
		error_msg = "null"
		query_who = dms._json['message_create']['sender_id']
		query_when = int(dms._json['created_timestamp'])
		if query_who != tweeterid and r < query_when:
			update_timestamp(query_when)
			query_data = dms._json['message_create']['message_data']['text']
			print("step B")
			print(query_data)
			if tweetlink_check(query_data) == True:
				query_datb = dms._json['message_create']['message_data']['entities']['urls'][0]['expanded_url']
				if youtubelink_check(query_datb) == True: 
					y = split_text(query_data)
					try: 
						if folder_check(y[1]) == False: 
							error_msg = "Folder not exist" 
							print("step C")
					except: error_msg = "Please provide folder"
				else: error_msg = "Problem with youtube link"
			else:
				if command_twitter_check(query_data) == False:
					error_msg = "Problem with twitter link"
				else:
					error_msg = "cmc"

			if error_msg  == "null":
				sql_insert(query_datb, y[1], query_who, query_when, "0")
			else:
				if error_msg != "cmc": send_dm(query_who, error_msg)
			if error_msg == "cmc": execute_command(query_who, query_data)



def split_text(txt):
	txt = txt.strip()
	x = re.sub(r'\s+', ' ', txt)
	split_text_value = x.split(" ")
	return split_text_value

def tweetlink_check(link):
	result = link.startswith('https://youtu.be') 
	if result == False: 
		result = link.startswith('https://youtube.com') 
		if result == False:
			result = link.startswith('https://t.co')
			if result == False:
			    result = link.startswith('https://www.youtube.com')
	return result

def command_twitter_check(txt):
	result = txt.startswith('#')
	return result

def youtubelink_check(link):
	result = link.startswith('https://youtu.be') 
	if result == False: 
		result = link.startswith('https://youtube.com')
		if result == False:
		    result = link.startswith('https://www.youtube.com')
	return result


def database_clean():
	with con:
		data = con.execute("SELECT * FROM DOWNLOAD WHERE execute == 0")
		for row in data:
			if youtubelink_check(row[1]) == False:
				sql_delete_row(row[0])
				print(row[1])
			if folder_check(row[2]) == False:
				sql_delete_row(row[0])
				print(row[2])

def folder_check(folder):
	return os.path.isdir(path+folder)

def file_move(file, folder):
	filename = file.split("/")
	shutil.move(file, path+folder+'/'+filename[1])

def send_dm(to, message):
	api.send_direct_message(to, message)

def send_towall(message):
	api.update_status(message)

def download_music(yt_link, folder):
	with yt_dlp.YoutubeDL(ydl_opts) as ydl:
		ydl.add_post_processor(MyCustomPP())
		info = ydl.extract_info(yt_link)
		jsons = ydl.sanitize_info(info)
		filepath = jsons['requested_downloads'][0]['filepath']
		idfile = jsons['id']
		file_move(filepath, folder)
		send_towall(jsons['title']+" downloaded to "+folder)


def check_database_download():
	with con:
		data = con.execute("SELECT * FROM DOWNLOAD WHERE execute == 0")
		for row in data:
			print(row)
			try:
				download_music(row[1], row[2])
				update_download(row[0])
				time.sleep(61)
			except:
				print('Error: Probably wrong YT link, deleting from sql')
				sql_delete_row(row[0])

def execute_command(query_who, txt):
	txt = txt.strip()
	s = txt.split("#")

	if s[1]=="help":
		print("command help executed")
		send_dm(query_who, "List of commands: help, listd")
	if s[1]=="listd":
		print("command listd executed")
		dirfiles = os.listdir(path)
		dirs = []
		files = []

		for file in dirfiles:
			if os.path.isdir(file): dirs.append(file)
			if os.path.isfile(file): files.append(file)

		listToStr = ' '.join([str(elem) for elem in dirs])
		strlenght = len(listToStr)
		if strlenght < 10000:
			send_dm(query_who, listToStr)
		else:
			print("Maximum twitter DM is 10000")


sql_prepare()

i = 1
while i < 2 :
	try:
		get_fromtwitter()
		print("evrything good, checking database")
		check_database_download()
		print("checking database done, we will wait 1 minute")
		time.sleep(61)
	except:
		print("ok we found an error and we will wait 15 minutes")
		time.sleep(901)

#end