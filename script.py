import imaplib
import base64
import os
import email
from db import MSSQLDB
import sys

class EmailManager:

	def __init__(self, db):
		self.db = db
		self.mail = None
		self.current_service = None

	def login(self, email_id, password):
		self.current_email_id = email_id

		# Determine server
		if email_id.endswith('@gmail.com') or email_id.endswith('@sitpune.edu.in'):
			self.current_service = 'GMAIL'
			host = "imap.gmail.com"
			try:
				self.mail = imaplib.IMAP4_SSL(host, 993)
				print (f'[+] Established connection with {self.current_service} IMAP...')
			except Exception as err:
				print ('[ERROR] Not able to establish connection with GMAIL IMAP...')
				return False
		elif email_id.endswith('@yahoo.com'):
			self.current_service = 'YAHOO'
			host = "imap.mail.yahoo.com"
			try:
				self.mail = imaplib.IMAP4_SSL(host, 993)
				print (f'[+] Established connection with {self.current_service} IMAP...')
			except Exception as err:
				print ('[ERROR] Not able to establish connection with GMAIL IMAP...')
				return False

		try:
			self.mail.login(email_id, password)
			print ('[+] Login successful')
		except Exception as err:
			print (f'[ERROR] Login Failed: {err}')
			return False

		return True

	def retrieve_ids_of_emails(self, date=None):
		try:
			self.mail.select()
			type, data = self.mail.search(None, 'ALL')
			mail_ids = data[0]
			return mail_ids.split()
		except Exception as err:
			print (f'[ERROR] There was an error in retrieving emails: {err}')
			return False

	def download_attachment(self, email_message):
		attachment_paths = []
		# downloading attachments
		for part in email_message.walk():
			# this part comes from the snipped I don't understand yet... 
			if part.get_content_maintype() == 'multipart':
				continue
			if part.get('Content-Disposition') is None:
				continue
			fileName = part.get_filename()
			if bool(fileName):
				filePath = os.path.join('./attachments/', fileName)
				if not os.path.isfile(filePath) :
					fp = open(filePath, 'wb')
					fp.write(part.get_payload(decode=True))
					fp.close()
				attachment_paths.append(filePath)
		if not all(attachment_paths) or len(attachment_paths) == 0:
			return False
		return str([i for i in attachment_paths if i != None])

	def parse_emails(self, eyeds, upto=50):
		arr = eyeds[::-1][:upto]
		total = len(arr)
		for index, num in enumerate(arr):
			email_data = {'id_for_service' : num.decode('utf-8'), 'service_name' : self.current_service}

			typ, data = self.mail.fetch(num, '(RFC822)' )
			raw_email = data[0][1]
			# converts byte literal to string removing b''
			raw_email_string = raw_email.decode('utf-8')
			email_message = email.message_from_string(raw_email_string)

			attachment_downloaded_path = self.download_attachment(email_message)

			subject = str(email_message).split("Subject: ", 1)[1].split("\nTo:", 1)[0].split('\n')[0]
			email_from = str(email_message).split("From: ", 1)[1].split("\nDate:", 1)[0].split('\n')[0]
			try:
				cc = str(email_message).split("Cc: ", 1)[1].split("\nContent-Type:", 1)[0].split('\n')[0]
				email_data['email_cc'] = cc
			except:
				pass
			date = str(email_message).split("Date: ", 1)[1].split("\nMessage-ID:", 1)[0].split('\n')[0]

			if attachment_downloaded_path:
				email_data['attachment_present'] = 1
				email_data['attachment_path'] = attachment_downloaded_path
			else:
				email_data['attachment_present'] = 0
			email_data['email_subject'] = subject
			email_data['email_from'] = email_from
			email_data['date'] = date
			status, message = self.db.insert_data(email_data)
			if status:
				print (f'[+] ---> Email {index + 1} / {total} inserted')
			else:
				print (f'[-] ---> Email {index + 1} / {total} NOT inserted. Duplicate email.')

if __name__ == '__main__':
    args = sys.argv

    try:
        email_id = sys.argv[1]
        password = sys.argv[2]
    except:
        exit("Invalid params.")
	db = MSSQLDB(conn_string="", database="")
    em = EmailManager(db=db)
    is_logged_in = em.login(email_id, password)
    if is_logged_in:
        eyeds = em.retrieve_ids_of_emails()
        em.parse_emails(eyeds)
   

