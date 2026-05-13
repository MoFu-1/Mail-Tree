'''
Split each email in the email chain and generate a unique node ID
'''

import json
import os
import re

# Regex for reply headers in Foxmail and common Chinese email providers (QQ, NetEase, etc.)
# Match "Sender: xxx" or "From: xxx" or "De : xxx"
SENDER_REGEX = re.compile(r'(?:Sender|From|De)\s*[:：]\s*(.+)', re.IGNORECASE)

# Match "Sent time: xxx" or "Date: xxx" or "Envoyé : xxx" etc.
DATE_REGEX = re.compile(r'(?:Time|Date|Sent|Envoyé|Enviado(?: el)?)\s*[:：]\s*(.+)', re.IGNORECASE)

# Match "To: xxx" etc.
TO_REGEX = re.compile(r'(?:收件人|To|À|Para)\s*[:：]\s*(.+)', re.IGNORECASE)

# Match "Cc: xxx" etc.
CC_REGEX = re.compile(r'(?:抄送|Cc)\s*[:：]\s*(.+)', re.IGNORECASE)

# 匹配并移除开头的所有引用头信息，支持多行折叠和字段间空行
HEADER_BLOCK_REGEX = re.compile(
    r'^\s*(?:(?:Sender|From|De|Time|Date|Sent|Envoyé|Enviado(?: el)?|收件人|To|À|Para|抄送|Cc|主题|Subject|Objet|Asunto)\s*[:：].*(?:\n[ \t]+.*)*\s*)+',
    re.IGNORECASE | re.MULTILINE
)

# Match signature separators or common signature identifiers
SIGNATURE_REGEX = re.compile(r'\n\s*(?:--+|___+|Best Regards\s*|Regards\s*,?|BR\r?\n|Thanks and best regards|Thank you!?|Thanks\s*,?\s*\n|发自.*|Sent from.*|获取 Outlook|Get Outlook|.*(?:Sales Manager|Director|Engineer)\s*\n|.*(?:\+86\s*\d{11}|1[3-9]\d{9}))', re.IGNORECASE)

# Match original email dividing lines or lookaheads for reply headers without separating lines
ORIGINAL_MAIL_SPLIT_REGEX = re.compile(r'(?:\n(?=(?:Sender|From|De)\s*[:：]))|(?:[-]{2,}\s*(?:Original|原始邮件|回复邮件|转发邮件|Original Message)\s*[-]{2,})', re.IGNORECASE)


def process_offline_mails(input_file="data/raw/mails.json", output_file="data/interim/mails_split.json"):
    print(f"Start reading: {input_file}...")
    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        mails = json.load(f)

    print(f"Total read {len(mails)} email records, preparing to split reply chains...")
    split_results = []

    for mail in mails:
        uid = mail.get("UID", "")
        main_sender = mail.get("Sender", "") or mail.get("Sender邮箱", "")
        main_time = mail.get("Time", "")
        body = mail.get("Content", "")

        chain = []
        parts = ORIGINAL_MAIL_SPLIT_REGEX.split(body)

        for idx, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue

            sender = ""
            time = ""
            to = ""
            cc = ""

            # Extract sender and time
            s_match = SENDER_REGEX.search(part)
            if s_match:
                sender = s_match.group(1).strip()

            d_match = DATE_REGEX.search(part)
            if d_match:
                time = d_match.group(1).strip()
                
            t_match = TO_REGEX.search(part)
            if t_match:
                to = t_match.group(1).strip()
                
            c_match = CC_REGEX.search(part)
            if c_match:
                cc = c_match.group(1).strip()

            if idx == 0 and not sender:
                sender = main_sender
                time = main_time
                to = mail.get("收件人", "") or ""
                cc = mail.get("抄送人", "") or ""

            # 剥离回复产生的 Header 快
            content = HEADER_BLOCK_REGEX.sub('', part).strip()

            # Separate signature
            signature = ""
            sig_match = SIGNATURE_REGEX.search("\n" + content)
            if sig_match:
                # Adjust index because \n was added
                sig_start = sig_match.start()
                if sig_start == 0 and len(content) > 0:
                    sig_start = max(0, sig_match.start() - 1)
                elif sig_start > 0:
                    sig_start -= 1
                    
                signature = content[sig_start:].strip()
                content = content[:sig_start].strip()

            chain.append({
                "uid": idx + 1,  # Incremental number within chain
                "layer": idx + 1,
                "sender": sender,
                "time": time,
                "to": to,
                "cc": cc,
                "content": content,
                "signature": signature
            })

        split_results.append({
            "message_id": mail.get("Message-ID", ""),
            "references": mail.get("References", ""),
            "in_reply_to": mail.get("In-Reply-To", ""),
            "uid": uid,
            "subject": mail.get("主题", ""),
            "chain": chain
        })

    print(f"Saving split results to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(split_results, f, ensure_ascii=False, indent=2)
    print(f"Save complete! Total generated {len(split_results)} records.")

if __name__ == "__main__":
    process_offline_mails()
