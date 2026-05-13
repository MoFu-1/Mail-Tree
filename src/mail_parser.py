import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
import re

class MailParser:
    @staticmethod
    def decode_str(s):
        """Decode email header string"""
        if not s:
            return ""
        decoded_list = decode_header(s)
        res = ""
        for text, charset in decoded_list:
            if isinstance(text, bytes):
                charset = charset or 'utf-8'
                if charset.lower() in ['gb2312', 'gbk']:
                    charset = 'gb18030'  # Use gb18030 to be compatible with gb2312 and gbk to avoid errors with special chars
                try:
                    res += text.decode(charset, errors='ignore')
                except LookupError:
                    res += text.decode('utf-8', errors='ignore')
            else:
                res += text
        return res

    @staticmethod
    def extract_body(msg):
        """Parse email body, prefer plain text, if not available extract HTML and strip tags"""
        body_plain = ""
        body_html = ""
        
        # For example
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Ignore attachments
                if "attachment" in content_disposition:
                    continue
                    
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    if content_type == "text/plain":
                        body_plain += part.get_payload(decode=True).decode(charset, errors='ignore')
                    elif content_type == "text/html":
                        body_html += part.get_payload(decode=True).decode(charset, errors='ignore')
                except Exception:
                    pass
        else:
            try:
                content_type = msg.get_content_type()
                charset = msg.get_content_charset() or 'utf-8'
                if content_type == "text/plain":
                    body_plain = msg.get_payload(decode=True).decode(charset, errors='ignore')
                elif content_type == "text/html":
                    body_html = msg.get_payload(decode=True).decode(charset, errors='ignore')
                else:
                    body_plain = msg.get_payload(decode=True).decode(charset, errors='ignore')
            except Exception:
                pass
                
        # Prefer returning plain text without tags
        if body_plain.strip():
            return body_plain.strip()
            
        # If only HTML is present, process it with simple tag stripping
        if body_html.strip():
            # Remove style and script code blocks inside <style> and <script>
            text = re.sub(r'<style.*?</style>', '', body_html, flags=re.IGNORECASE|re.DOTALL)
            text = re.sub(r'<script.*?</script>', '', text, flags=re.IGNORECASE|re.DOTALL)
            # Remove common HTML tags and messy newline formats
            text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'</?(div|p|tr|td|li)[^>]*>', '\n', text, flags=re.IGNORECASE)
            text = re.sub(r'<[^>]+>', '', text)
            # Decode HTML entities like &nbsp;
            text = text.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')
            # Compress excessive whitespace and newlines
            text = re.sub(r'\n\s*\n', '\n', text)
            return text.strip()
            
        return ""

    def parse(self, raw_email_bytes):
        """
        Parse raw email bytes and return dictionary data: Time, Sender, SenderEmail, Cc, Content
        """
        msg = email.message_from_bytes(raw_email_bytes)
        
        # 1. Extract Sender
        from_str = msg.get("From", "")
        from_name, from_addr = parseaddr(from_str)
        sender_name = self.decode_str(from_name)
        
        # 2. Extract To
        to_str = msg.get("To", "")  #"Delivered-To"
        to_decoded = self.decode_str(to_str) if to_str else ""
        
        # 3. Extract CC
        cc_str = msg.get("Cc", "")
        cc_decoded = self.decode_str(cc_str) if cc_str else ""
        
        # 4. Extract Time
        date_str = msg.get("Date", "")
        formatted_date = date_str
        if date_str:
            try:
                dt = parsedate_to_datetime(date_str)
                # Convert to common string format YYYY-MM-DD HH:MM:SS
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                formatted_date = date_str
        
        # Parse attachments
        attachments = []
        import os
        attachment_dir = os.path.join("data", "attachments")
        os.makedirs(attachment_dir, exist_ok=True)
        
        if msg.is_multipart():
            for part in msg.walk():
                # Ignore multiparts themselves or dependent parts
                if part.get_content_maintype() == 'multipart':
                    continue
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" not in content_disposition:
                    continue
                
                filename = part.get_filename()
                if filename:
                    filename = self.decode_str(filename)
                    # Clean illegal chars that might cause path issues
                    safe_filename = "".join(c for c in filename if c not in r'\/:*?"<>|')
                    save_path = os.path.join(attachment_dir, safe_filename)
                    
                    try:
                        with open(save_path, "wb") as f:
                            f.write(part.get_payload(decode=True))
                        attachments.append(safe_filename)
                    except Exception as e:
                        print(f"Save attachment {safe_filename} failed: {e}")

        # Extract reply-related info and subject
        message_id = msg.get("Message-ID", "").strip() if msg.get("Message-ID") else ""
        in_reply_to = msg.get("In-Reply-To", "").strip() if msg.get("In-Reply-To") else ""
        references = msg.get("References", "").strip() if msg.get("References") else ""
        subject = self.decode_str(msg.get("Subject", ""))

        # 4. Extract main body content
        body = self.extract_body(msg)
        
        return {
            "Message-ID": message_id,
            "In-Reply-To": in_reply_to,
            "References": references,
            "Subject": subject,
            "Time": formatted_date,
            "Sender": sender_name if sender_name else from_addr,
            "SenderEmail": from_addr,
            "To": to_decoded,
            "Cc": cc_decoded,
            "Content": body,  # 1000 chars truncation removed
            "AttachmentNames": ", ".join(attachments)
        }
