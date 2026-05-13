PROTOCOL = "IMAP" # 'IMAP' or 'POP3'

# IMAP Settings (QQ Mail defaults as requested)
IMAP_SERVER = "imap.qq.com"
IMAP_PORT = 993

# POP3 Settings
POP3_SERVER = "your_pop3_server.com"
POP3_PORT = 995

EMAIL_ACCOUNT = "your_email@example.com"
# Fill in email authorization code here (Do NOT commit to repository)
EMAIL_PASSWORD ="your_email_auth_code"

# ==========================================
# Business Workflow Parameters
# ==========================================
# Maximum number of emails to fetch each time
EMAIL_FETCH_LIMIT = 50

# Data Access Path Settings
PATH_DATA_DIR = "data"
PATH_RAW_JSON = "data/raw/mails.json"
PATH_INTERIM_SPLIT = "data/interim/mails_split.json"
PATH_OUTPUT_HEADERS = "data/output/mails_tree_headers.json"
PATH_OUTPUT_DIR = "data/output"
PATH_OUTPUT_HTML = "email_tree.html"