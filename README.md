# 🌳 MailTree
MailTree is a tool designed to solve the problem of scattered and difficult-to-track email reply chains. By parsing and organizing emails into structured threads and trees, MailTree helps users **easily understand the context, flow, and branches of email discussion**s. It can be used for **email cleaning, email summarization, and extracting the most complete email threads**.

## ✨ Key Features / Problem Solving Approaches
###  1. Email Tree Reconstruction
Constructs an email tree from bottom to top using `Message-ID`, `In-Reply-To`, and `References` headers. This visualizes all nodes and identifies missing or **"Ghost Nodes"**.

###  2. Ghost Node Interpolation
In branching structures, if intermediate emails are missing locally, MailTree inserts **"Ghost Nodes"** to maintain structural integrity and estimates their properties using interpolations.

###  3. Zero External Dependencies
Uses only standard library modules:
`os` · `sys` · `json` · `re` · `datetime` · `collections (defaultdict)` · `glob` · `poplib` · `imaplib`

###  4. Full POP3 / IMAP Support
Fetch emails directly from your mail server using industry-standard protocols.

---


## 🗺️ Where can it be applied?
### 1. 🪙 Reduce Token Consumption & Enhance AI Summarization
By aggregating historical emails into a thread tree, redundant content (like repeated signatures and quoted replies) is eliminated. This provides the AI with a more comprehensive, streamlined context, significantly improving the quality and accuracy of the generated summaries.

### 2. 🤖 Improve AI Autonomous Reply Capabilities *(Future Outlook)*
By analyzing large-scale thread trees, the system can help you or the AI identify specific patterns — determining which types of emails require which specific styles of response based on historical context.

### 3. 🔍 Retrospective Review of Project History
If you rely on email for work, you will inevitably encounter "he-said-she-said" disputes. This project helps you reconstruct the chronological development of events. By analyzing response intervals, you can easily identify bottlenecks — such as who was slow to respond or which specific incident caused a project delay.

----

## 💡 Background & Core Concepts
Emails often consist of multiple sub-emails (replies), forming a chain (e.g., `M1 → M2 → M3 → M4`). When different people reply to the same email, branches are created, forming a **tree structure** rather than a simple chain.

Case 1: Email Chain
M1 - M2 - M3

Case 2: Email Tree
```
M1
├── M2 → M4 
├── M2 → M5
└── M3 → M6
```
Wherein, Case 2 can be simplified and synthesized into:
```
        M1
       /  \
      M2   M3
     / \     \
    M4  M5   M6
```
----


```
📁 MailTree/
│
├── 🐍 main.py                        # Single entry point for the application
│
├── ⚙️  config/
│   ├── __init__.py
│   └── settings.py                   # Environment parameters and configurations
│
├── 📂 data/
│   ├── raw/                          # Raw, unparsed/unprocessed emails
│   ├── interim/                      # Intermediate artifacts (e.g., split emails)
│   └── output/                       # Final generated outputs (e.g., email trees, HTML visualization)
│
└── 🔧 src/
    ├── preprocess/
    │   ├── __init__.py
    │   ├── mail_splitter.py          # Parses offline emails and extracts replies/signatures
    │   └── build_tree_headers.py     # Combines messages using headers (In-Reply-To, References)
    │
    ├── mail_client.py                # 📡 POP3/IMAP client to fetch emails
    ├── mail_parser.py                # 🔍 Parses raw email bytes into structured dictionaries
    ├── tree_builder.py               # 🌳 Builds the final tree relationships from chains/messages
    └── visualizer.py                 # 🎨 Generates the D3.js interactive HTML visualization

📁 frontend/
└── tree_logic.js                     # 📊 D3 tree rendering logic injected into the visualizer
```

---

## 🚀 Quick Start
**Step 1 — Configure credentials**
Provide your email credentials + configurations in `config/settings.py`.

**Step 2 — Run**
```bash
python main.py
```
This will automatically **fetch → parse → rebuild the thread tree → generate** an interactive `email_tree.html` visualization in the `data/output/` directory.

> 📝 **Note:** The visualization part is still in testing — other visualization ideas are welcome!
