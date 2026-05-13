# -*- coding: utf-8 -*-
import sys
import json
import os
from config import settings
from src.mail_client import MailClient
from src.mail_parser import MailParser
from src.tree_builder import TreeBuilder
from src.visualizer import HTMLVisualizer

from src.preprocess.mail_splitter import process_offline_mails
from src.preprocess.build_tree_headers import build_tree

def main():
    print("Connecting to mailbox...")
    client = MailClient()
    
    # Ensure directories exist
    os.makedirs(os.path.dirname(settings.PATH_RAW_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(settings.PATH_INTERIM_SPLIT), exist_ok=True)
    os.makedirs(settings.PATH_OUTPUT_DIR, exist_ok=True)
    
    try:
        # 1. Login
        client.login()
        
        # 2. Fetch emails
        print("Fetching latest emails...")
        raw_emails = client.fetch_emails(limit=settings.EMAIL_FETCH_LIMIT)
        print(f"Total fetched {len(raw_emails)} emails, ready to parse.")
        
        # 3. Parse emails
        parser = MailParser()
        parsed_data = []
        for uid_str, raw_bytes in raw_emails:
            data = parser.parse(raw_bytes)
            data["UID"] = uid_str
            parsed_data.append(data)
            
        json_filename = settings.PATH_RAW_JSON
        
        # Incremental update of JSON file
        if os.path.exists(json_filename):
            try:
                with open(json_filename, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    parsed_data = existing_data + parsed_data
            except Exception as e:
                print(f"Exception reading existing JSON:{e}")
                
        if parsed_data:
            print(f"Exporting structured data to JSON: {json_filename}...")
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)

        client.logout()
        print("Disconnected from mailbox.")

        # 4. Execute preprocessing script: Split emails
        print("Executing email split...")
        process_offline_mails(input_file=settings.PATH_RAW_JSON, output_file=settings.PATH_INTERIM_SPLIT)
        
        # 5. Execute preprocessing script: Build tree based on Headers
        print("Building Header reference relationships tree...")
        build_tree(input_file=settings.PATH_INTERIM_SPLIT, output_file=settings.PATH_OUTPUT_HEADERS)

        # 6. Build reply tree and generate visual chart
        print("Building reply tree and generating interactive HTML chart...")
        try:
            tree_builder = TreeBuilder()
            
            # Build tree using split data if TreeBuilder supports it
            if os.path.exists(settings.PATH_INTERIM_SPLIT):
                with open(settings.PATH_INTERIM_SPLIT, "r", encoding="utf-8") as f:
                    tree_data = json.load(f)
            else:
                tree_data = parsed_data
                
            roots = tree_builder.build_tree(tree_data)
            
            visualizer = HTMLVisualizer(output_dir=settings.PATH_OUTPUT_DIR)
            visualizer.generate_d3_html(roots, filename=settings.PATH_OUTPUT_HTML)
        except Exception as ve:
            print(f"Visualization generation failed: {ve}")
        
    except Exception as e:
        print(f"Program execution interrupted: {e}")
    finally:
        print("Execution completed!")

if __name__ == "__main__":
    main()