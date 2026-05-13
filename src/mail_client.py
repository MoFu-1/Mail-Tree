import poplib
import imaplib
from config import settings
import os
import json
import glob

class MailClient:
    def __init__(self):
        self.protocol = getattr(settings, "PROTOCOL", "POP3").upper()
        if self.protocol == "IMAP":
            self.mail = imaplib.IMAP4_SSL(settings.IMAP_SERVER, getattr(settings, "IMAP_PORT", 993))
        else:
            self.mail = poplib.POP3_SSL(settings.POP3_SERVER, settings.POP3_PORT)
        
        self._load_processed_uids()

    def _load_processed_uids(self):
        self.processed_uids = set()
        data_dir = settings.PATH_DATA_DIR
        if not os.path.exists(data_dir):
            return
            
        json_files = glob.glob(os.path.join(data_dir, "**", "mails*.json"), recursive=True)
        for filepath in json_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            uid = item.get("UID")
                            if uid:
                                self.processed_uids.add(str(uid))
            except Exception as e:
                pass

    def login(self):
        """Login to mailbox"""
        try:
            if self.protocol == "IMAP":
                self.mail.login(settings.EMAIL_ACCOUNT, settings.EMAIL_PASSWORD)
                self.mail.select("INBOX")
            else:
                self.mail.user(settings.EMAIL_ACCOUNT)
                self.mail.pass_(settings.EMAIL_PASSWORD)
            print(f"[{self.protocol}] Login successful!")
        except Exception as e:
            print(f"Login failed, check account and password/auth code. Error: {e}")
            raise e

    def fetch_emails(self, limit=20):
        """
        Fetch raw data of the most recent limit emails
        """
        if self.protocol == "IMAP":
            return self._fetch_imap(limit)
        else:
            return self._fetch_pop3(limit)

    def _fetch_imap(self, limit):
        try:
            # Search UIDs of all emails
            status, response = self.mail.uid('search', None, "ALL")
            if status != 'OK':
                print("Failed to get email list")
                return []
                
            uids = response[0].split()
        except Exception as e:
            print(f"IMAPFailed to get email list: {e}")
            return []

        if not uids:
            return []

        # Filter out unprocessed UIDs
        unprocessed = [uid for uid in uids if uid.decode('utf-8') not in self.processed_uids]
        print(f"Total {len(uids)} emails, of which {len(unprocessed)} emails pending to fetch.")

        # Take the latest limit unprocessed emails
        target_uids = unprocessed[-limit:]
        target_uids.reverse()
        
        raw_emails = []
        for uid in target_uids:
            try:
                status, data = self.mail.uid('fetch', uid, '(RFC822)')
                if status == 'OK':
                    for response_part in data:
                        if isinstance(response_part, tuple):
                            uid_str = uid.decode('utf-8')
                            raw_emails.append((uid_str, response_part[1]))
                            self.processed_uids.add(uid_str)
            except Exception as e:
                print(f"Fetching email (UID: {uid}) failed: {e}")
                continue
                
        return raw_emails

    def _fetch_pop3(self, limit):
        try:
            # POP3 LIST
            _, message_list, _ = self.mail.list()
            # POP3 UIDL
            _, uid_list, _ = self.mail.uidl()
        except poplib.error_proto:
            print("Failed to get email list")
            return []

        if not message_list or not uid_list:
            return []

        email_info = []
        for item, uid_item in zip(message_list, uid_list):
            try:
                msg_id = int(item.decode(errors="ignore").split()[0])
                uid_str = uid_item.decode(errors="ignore").split()[1]
                email_info.append((msg_id, uid_str))
            except Exception:
                continue

        # Filter out unprocessed UIDs
        unprocessed = [(msg_id, uid) for msg_id, uid in email_info if uid not in self.processed_uids]
        print(f"Total {len(email_info)} emails, of which {len(unprocessed)} emails pending to fetch.")

        # Take the latest limit unprocessed emails
        target_info = unprocessed[-limit:]
        target_info.reverse()
        
        raw_emails = []
        for msg_id, uid in target_info:
            try:
                _, lines, _ = self.mail.retr(msg_id)
                raw_emails.append((uid, b"\r\n".join(lines)))
                self.processed_uids.add(uid)
            except poplib.error_proto:
                continue
        return raw_emails

    def logout(self):
        """Logout"""
        try:
            if self.protocol == "IMAP":
                self.mail.close()
                self.mail.logout()
            else:
                self.mail.quit()
        except:
            pass