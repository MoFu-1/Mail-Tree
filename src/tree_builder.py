import json
from collections import defaultdict
import re

class TreeBuilder:
    def __init__(self):
        pass

    def build_tree(self, data, top_n=None):
        if isinstance(data, list) and len(data) > 0 and 'chain' in data[0]:
            return self._build_tree_from_chains(data, top_n)
        else:
            return self._build_tree_from_messages(data, top_n)

    def _build_tree_from_chains(self, split_data, top_n=None):
        class Node:
            def __init__(self, sender, time, content, uid, subject, to='', cc=''):
                self.sender = sender
                self.time = time
                self.content = content
                self.uid = uid
                self.subject = subject
                self.to = to
                self.cc = cc
                self.children_dict = {}  
                self.children = []       

            def to_dict(self):
                return {
                    'Sender': self.sender,
                    'Time': self.time,
                    'To': self.to,
                    'Cc': self.cc,
                    'Content': self.content,
                    'Subject': self.subject,
                    'UID': self.uid,
                    'children': [c.to_dict() for c in self.children]
                }

        def get_node_key(layer):
            content = str(layer.get('content', ''))
            content = re.sub(r'(?i)^(?:回复|转发|re|fw|fwd)\s*[:：]\s*', '', content)
            content = re.sub(r'(?i)(?:Sender|from|To|to|Time|date|Subject|subject)\s*[:：].*?(?:\n|$)', '', content)
            c_clean = ''.join(content.split())[:50]

            sender = str(layer.get('sender', ''))
            email_match = re.search(r'[\w\.-]+@[a-zA-Z0-9\.-]+', sender)
            s_clean = email_match.group(0).lower() if email_match else ''.join(sender.split()).lower()
            
            return (s_clean, c_clean)

        roots = {}

        for mail in split_data:
            subject = mail.get("subject", "")
            chain = mail.get("chain", [])
            if not chain:
                continue

            chain_reversed = list(reversed(chain))

            current_nodes = roots
            for layer in chain_reversed:
                key = get_node_key(layer)
                if key not in current_nodes:
                    content = layer.get('content', '')
                    if layer.get('signature'):
                        content += '\n\n' + layer.get('signature')

                    node = Node(
                        sender=layer.get('sender', ''),
                        time=layer.get('time', ''),
                        content=content,
                        uid=layer.get('uid', ''),
                        subject=subject,
                        to=layer.get('to', ''),
                        cc=layer.get('cc', '')
                    )
                    current_nodes[key] = node

                parent_node = current_nodes[key]
                current_nodes = parent_node.children_dict

        def collect_nodes(dict_nodes):
            node_list = []
            for key, node in dict_nodes.items():
                node.children = collect_nodes(node.children_dict)
                node_list.append(node)
            return node_list

        root_list = collect_nodes(roots)
        converted_roots = [n.to_dict() for n in root_list]

        converted_roots.sort(key=self._count_nodes, reverse=True)
        if top_n is not None and top_n > 0:
            converted_roots = converted_roots[:top_n]
        return converted_roots

    def _build_tree_from_messages(self, emails, top_n=None):
        email_dict = {}
        for mail in emails:
            msg_id = mail.get("Message-ID")
            if msg_id:
                msg_id = msg_id.strip()
                email_dict[msg_id] = mail
                email_dict[msg_id]["children"] = []
            else:
                temp_id = f"temp_{id(mail)}"
                email_dict[temp_id] = mail
                email_dict[temp_id]["children"] = []
                mail["Message-ID"] = temp_id

        root_nodes = []
        for msg_id, mail in email_dict.items():
            in_reply_to = mail.get("In-Reply-To")
            parent_id = None

            if in_reply_to:
                parts = in_reply_to.split()
                if parts:
                    parent_id = parts[0].strip()
            elif mail.get("References"):
                parts = mail.get("References").split()
                if parts:
                    parent_id = parts[-1].strip()

            if parent_id and parent_id in email_dict:
                email_dict[parent_id]["children"].append(mail)
            else:
                root_nodes.append(mail)

        self._sort_children_by_time(root_nodes)

        root_nodes.sort(key=self._count_nodes, reverse=True)
        if top_n is not None and top_n > 0:
            root_nodes = root_nodes[:top_n]

        return root_nodes

    def _count_nodes(self, node):
        count = 1
        if "children" in node and node["children"]:
            for child in node["children"]:
                count += self._count_nodes(child)
        return count

    def _sort_children_by_time(self, nodes):
        for node in nodes:
            if "children" in node and node["children"]:
                node["children"].sort(key=lambda x: x.get("Time", ""))      
                self._sort_children_by_time(node["children"])
