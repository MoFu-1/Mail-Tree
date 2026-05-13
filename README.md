# MailTree

MailTree is a tool designed to solve the problem of scattered and difficult-to-track email reply chains. By parsing and organizing emails into structured threads and trees, MailTree helps users easily understand the context, flow, and branches of email discussions. It can be used for email cleaning, email summarization, and extracting the most complete email threads.


## Where can it be applied?
1. Reduce Token consumption and enhance AI summarization.
By aggregating historical emails into a thread tree, redundant content (like repeated signatures and quoted replies) is eliminated. This provides the AI with a more comprehensive, streamlined context, significantly improving the quality and accuracy of the generated summaries.

2. Improve AI autonomous reply capabilities (Future Outlook):
By analyzing large-scale thread trees, the system can help you or the AI identify specific patterns—determining which types of emails require which specific styles of response based on historical context.

3. Retrospective review of project history.
If you rely on email for work, you will inevitably encounter "he-said-she-said" disputes. This project helps you reconstruct the chronological development of events. By analyzing response intervals, you can easily identify bottlenecks—such as who was slow to respond or which specific incident caused a project delay.


## Background & Core Concepts

Emails often consist of multiple sub-emails (replies), forming a chain (e.g., M1 -> M2 -> M3 -> M4). When different people reply to the same email, branches are created, forming a tree structure rather than a simple chain.

## Key Features / Problem Solving Approaches:
1. Email Tree Reconstruction: Constructs an email tree from bottom to top using Message-ID, In-Reply-To, and References headers. This visualizes all nodes and identifies missing or "Ghost Nodes".
2. Filtering & Categorization: Allows for filtering by time, participants, and keywords to reduce the scope of emails and summarize content efficiently.
3. Ghost Node Interpolation: In branching structures, if intermediate emails are missing locally, MailTree inserts "Ghost Nodes" to maintain the structural integrity and estimates their properties using interpolations.
4. Uses only standard library modules like following: 
   os, sys, json, re, datetime, collections (defaultdict), glob, poplib, imaplib
5. Full POP3/IMAP Support
  

## Project Structure

`
main.py                        # Single entry point for the application
config/
  __init__.py
  settings.py                  # Environment parameters and configurations
data/
  raw/                         # Raw, unparsed/unprocessed emails
  interim/                     # Intermediate artifacts (e.g., split emails)
  output/                      # Final generated outputs (e.g., email trees, HTML visualization)
src/
  preprocess/
    __init__.py
    mail_splitter.py           # Parses offline emails and extracts replies/signatures
    build_tree_headers.py      # Combines messages using headers (In-Reply-To, References)
  mail_client.py               # POP3/IMAP client to fetch emails
  mail_parser.py               # Parses raw email bytes into structured dictionaries
  tree_builder.py              # Builds the final tree relationships from chains/messages
  visualizer.py                # Generates the D3.js interactive HTML visualization
frontend/
  tree_logic.js                # D3 tree rendering logic injected into the visualizer
`

## Quick Start

1. Provide your email credentials + configurations in config/settings.py.
2. Run python main.py to automatically fetch, parse, rebuild the thread tree, and generate an interactive email_tree.html visualization in the data/output/ directory.
Note: visualization part is still in testing, other visualization ideas are welcome!