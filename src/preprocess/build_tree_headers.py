import json
import os
import re
from datetime import datetime

def parse_date(date_str):
    if not date_str: return None
    date_str = str(date_str)
    # yyyy-mm-dd HH:MM:SS
    m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?", date_str)
    if m:
        parts = [int(x) for x in m.groups() if x is not None]
        if len(parts) == 5:
            parts.append(0)
        return datetime(*parts)
    return None

def extract_message_ids(header_val):
    if not header_val:
        return []
    # 匹配所有的 <xxxxx>
    return re.findall(r'<[^>]+>', header_val)

def build_tree(input_file="data/interim/mails_split.json", output_file="data/output/mails_tree_headers.json"):
    print(f"Reading from {input_file}...")
    if not os.path.exists(input_file):
        print("File not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        mails = json.load(f)

    # Extract required data
    # To build the tree, we need to flatten the information in mails_split.json (or use its structure directly, depending on node granularity)
    # But "message_id" in mails_split is for the email itself (including multi-layer reply chains)
    # The true tree is constructed via email-level Message-ID and In-Reply-To.
    # According to requirement: build email tree and calculate time interval between adjacent child emails.
    
    # Build mapping from ID to Email
    id_map = {}
    for mail in mails:
        msg_id = mail.get("message_id", "").strip()
        if not msg_id:
            # Try to get self from references, or generate virtual ID
            pass
        if msg_id:
            id_map[msg_id] = mail
            
    # Parse reference relationships and handle ghost nodes
    for mail in mails:
        refs = extract_message_ids(mail.get("references", ""))
        in_reply_to = mail.get("in_reply_to", "").strip()
        
        # In-Reply-To may contain multiple items, or just a simple string
        in_reply_match = extract_message_ids(in_reply_to)
        parent_id = in_reply_match[0] if in_reply_match else None
        
        # If no in_reply_to, try using the last item in references as parent
        if not parent_id and refs:
            parent_id = refs[-1]
            
        mail["parsed_parent_id"] = parent_id
        
        # Handle ghost nodes: add nodes from references
        prev_ref = None
        for ref in refs:
            if ref not in id_map:
                # Insert ghost node
                ghost_node = {
                    "message_id": ref,
                    "is_ghost": True,
                    "parsed_parent_id": prev_ref,
                    "uid": "GHOST_" + ref.strip('<>'),
                    "chain": [],
                    "subject": "Missing Email",
                }
                id_map[ref] = ghost_node
            elif prev_ref and not id_map[ref].get("parsed_parent_id"):
                id_map[ref]["parsed_parent_id"] = prev_ref
            prev_ref = ref
            
    # Secondary pass to assign parent attribute and build tree shape
    # Since JSON does not support circular references, we record using parent_id, or generate children list
    all_nodes = list(id_map.values())
    
    # Build children
    for node in all_nodes:
        node["children_ids"] = []
        
    for node in all_nodes:
        pid = node.get("parsed_parent_id")
        if pid and pid in id_map:
            id_map[pid]["children_ids"].append(node["message_id"])

    # Calculate time interval (need to get time of current email, corresponding to chain[0] i.e. latest reply time)
    for node in all_nodes:
        # Get own time
        t_self = None
        if "chain" in node and len(node["chain"]) > 0:
            t_self = parse_date(node["chain"][0].get("time"))
        node["parsed_time"] = t_self

    for node in all_nodes:
        pid = node.get("parsed_parent_id")
        if pid and pid in id_map and not node.get("is_ghost", False):
            parent_node = id_map[pid]
            t_parent = parent_node.get("parsed_time")
            t_self = node.get("parsed_time")
            # if t_parent and t_self:
            #     diff = t_self - t_parent
            #     node["intervalTime_hours"] = round(diff.total_seconds() / 3600.0, 2)
            # else:
            #     node["intervalTime_hours"] = None
        
        # Remove non-serializable datetime
        if "parsed_time" in node:
            del node["parsed_time"]
            
    # Output only node list structure, or return as forest based on root nodes
    print(f"Generated {len(all_nodes)} nodes (including ghosts). Saving...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_nodes, f, ensure_ascii=False, indent=4)
        
    print(f"Done. File saved to {output_file}")

if __name__ == "__main__":
    build_tree()
