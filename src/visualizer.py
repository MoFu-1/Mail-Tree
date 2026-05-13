import json
import os

class HTMLVisualizer:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def generate_d3_html(self, tree_data, filename="email_tree.html"):
        """
        Generate an HTML file containing a D3.js interactive tree diagram.
        """
        def convert_to_d3_format(node):
            name = node.get("Subject", "No Subject")
            if not name.strip():
                name = node.get("Message-ID") or node.get("UID", "Unknown Email")
            sender = node.get("Sender", "")
            time_str = node.get("Time", "")
            
            content_str = str(node.get("Content", ""))
            # Take first sentence or first 20 chars as abstract
            abstract_str = content_str.strip().split("\n")[0] if content_str else ""
            if len(abstract_str) > 20:
                abstract_str = abstract_str[:20] + "..."

            d3_node = {
                "name": f"{sender}: {name}" if sender.strip() else name,
                "sender": sender.strip(),
                "subject": name.strip(),
                "time": time_str,
                "abstract": abstract_str,
                "to": node.get("To", ""),
                "cc": node.get("Cc", ""),
                "content": content_str,  # Keep all content for future modal popup
                "msg_id": node.get("Message-ID") or node.get("UID", "")
            }
            if "children" in node and node["children"]:
                d3_node["children"] = [convert_to_d3_format(child) for child in node["children"]]
            return d3_node

        if len(tree_data) == 1:
            d3_data = convert_to_d3_format(tree_data[0])
        else:
            d3_data = {
                "name": "All Email Conversations",
                "time": "",
                "children": [convert_to_d3_format(root) for root in tree_data]
            }

        json_data = json.dumps(d3_data, ensure_ascii=False)

        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Email Reply Relationship Tree (D3.js)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-bg: #fcfcfd;
            --color-surface: #ffffff;
            --color-border: #eaecf0;
            --color-border-hover: #d0d5dd;
            --color-primary-bg: #f9fafb;
            --color-primary-hover: #f2f4f7;
            --color-primary-active: #101828;
            --color-primary-active-text: #ffffff;
            --color-text: #101828;
            --color-muted: #667085;
            --color-node-bg: #ffffff;
            --color-node-border: #eaecf0;
            --color-node-highlight: #fef08a; 
            --color-node-highlight-border: #fde047;
            --color-node-text: #344054;
            --radius-md: 8px;
            --radius-lg: 12px;
            --font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --shadow-sm: 0 1px 2px 0 rgba(16, 24, 40, 0.05);
            --shadow-md: 0 4px 8px -2px rgba(16, 24, 40, 0.1), 0 2px 4px -2px rgba(16, 24, 40, 0.06);
            --shadow-lg: 0 12px 16px -4px rgba(16, 24, 40, 0.08), 0 4px 6px -2px rgba(16, 24, 40, 0.03);
            --shadow-modal: 0 20px 24px -4px rgba(16, 24, 40, 0.08), 0 8px 8px -4px rgba(16, 24, 40, 0.03);
        }

        body { 
            font-family: var(--font-family); 
            background-color: var(--color-bg); 
            color: var(--color-text);
            margin: 0; 
            padding: 0; 
            display: flex; 
            height: 100vh; 
            overflow: hidden; 
            -webkit-font-smoothing: antialiased;
        }

        #sidebar { 
            width: 320px; 
            background: var(--color-surface); 
            border-right: 1px solid var(--color-border);
            padding: 24px; 
            box-sizing: border-box; 
            overflow-y: auto; 
            display: flex; 
            flex-direction: column; 
            gap: 16px; 
            box-shadow: var(--shadow-sm);
            z-index: 2;
        }
        
        #sidebar h4 {
            margin: 0 0 8px 0;
            font-size: 16px;
            font-weight: 600;
            color: var(--color-text);
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .input-group label {
            font-size: 13px;
            font-weight: 500;
            color: var(--color-text);
        }

        input[type="text"], select {
            width: 100%; 
            padding: 10px 12px; 
            box-sizing: border-box; 
            border: 1px solid var(--color-border); 
            border-radius: var(--radius-md); 
            font-family: var(--font-family);
            font-size: 14px;
            color: var(--color-text);
            background-color: var(--color-surface);
            transition: all 0.2s ease;
            outline: none;
            box-shadow: var(--shadow-sm);
        }

        input[type="text"]:focus, select:focus {
            border-color: var(--color-border-hover);
            box-shadow: 0 0 0 3px rgba(234, 236, 240, 0.5);
        }

        .sender-group { 
            padding: 12px 16px; 
            border: 1px solid var(--color-border); 
            border-radius: var(--radius-md); 
            margin-bottom: 8px; 
            cursor: pointer; 
            background: var(--color-surface); 
            font-size: 14px;
            font-weight: 500;
            color: var(--color-text);
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
        }

        .sender-group:hover { 
            background: var(--color-primary-hover);
            border-color: var(--color-border-hover);
            transform: translateY(-1px);
        }

        .sender-group.active { 
            background: var(--color-primary-active); 
            color: var(--color-primary-active-text);
            border-color: var(--color-primary-active); 
            box-shadow: var(--shadow-md);
        }

        #main-content { 
            flex: 1; 
            display: flex; 
            flex-direction: column; 
            position: relative;
        }

        #toolbar { 
            padding: 16px 24px; 
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(8px);
            border-bottom: 1px solid var(--color-border); 
            display: flex; 
            gap: 16px; 
            align-items: center; 
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            z-index: 10;
        }

        #toolbar select {
            width: auto;
            min-width: 140px;
        }

        button {
            padding: 10px 16px;
            background: var(--color-surface);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
            font-family: var(--font-family);
            font-size: 14px;
            font-weight: 500;
            color: var(--color-text);
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
        }

        button:hover {
            background: var(--color-primary-hover);
            border-color: var(--color-border-hover);
        }

        button:active {
            transform: scale(0.98);
        }

        #tree-container { 
            flex: 1; 
            overflow: auto; 
            background: var(--color-primary-bg); 
            cursor: grab; 
            /* Push content down to account for absolute toolbar */
            padding-top: 70px; 
            box-sizing: border-box;
        }

        #tree-container:active {
            cursor: grabbing;
        }

        .node circle { 
            fill: var(--color-surface); 
            stroke: var(--color-border); 
            stroke-width: 2px;
            transition: stroke 0.2s ease;
        }

        .node .node-rect { 
            fill: var(--color-node-bg); 
            stroke: var(--color-node-border); 
            rx: var(--radius-md); 
            ry: var(--radius-md); 
            transition: all 0.3s ease;
            filter: drop-shadow(0 1px 2px rgba(16, 24, 40, 0.05));
        }

        .node text { 
            font: 12px var(--font-family); 
            fill: var(--color-node-text);
            pointer-events: none;
        }

        .link { 
            fill: none; 
            stroke: #d0d5dd; 
            stroke-width: 1.5px; 
            transition: all 0.3s ease;
        }

        .time-axis text {
            font-size: 10px;
            color: var(--color-muted);
        }

        .time-axis path, .time-axis line {
            stroke: var(--color-border);
        }

        /* Modal */
        .modal {
            display: none; 
            position: fixed; 
            z-index: 1000; 
            left: 0; 
            top: 0; 
            width: 100%; 
            height: 100%;
            background-color: rgba(16, 24, 40, 0.4);
            backdrop-filter: blur(4px);
            animation: fadeIn 0.2s ease;
        }

        .modal-content {
            background-color: var(--color-surface); 
            margin: 4% auto; 
            padding: 32px;
            border: 1px solid var(--color-border); 
            width: 70%; 
            max-width: 800px;
            box-shadow: var(--shadow-modal);
            border-radius: var(--radius-lg); 
            max-height: 85vh; 
            overflow-y: auto;
            position: relative;
            animation: slideUp 0.3s ease;
        }

        .close { 
            color: var(--color-muted); 
            position: absolute;
            top: 24px;
            right: 24px;
            font-size: 24px; 
            font-weight: 500; 
            cursor: pointer;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--radius-md);
            transition: all 0.2s ease;
        }

        .close:hover { 
            color: var(--color-text); 
            background: var(--color-primary-hover);
        }

        #modal-title {
            margin: 0 0 8px 0;
            font-size: 20px;
            font-weight: 600;
            color: var(--color-text);
            padding-right: 40px;
            line-height: 1.4;
        }

        .modal-field {
            color: var(--color-muted); 
            font-size: 13px; 
            margin: 0 0 5px 0;
        }

        hr {
            border: 0;
            border-top: 1px solid var(--color-border);
            margin: 16px 0;
        }

        .modal-body { 
            white-space: pre-wrap; 
            font-family: 'Inter', monospace; 
            color: var(--color-text); 
            line-height: 1.6; 
            font-size: 14px;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
    </style>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <div id="sidebar">
        <h4>按Sender分组搜索与过滤</h4>
        <div class="input-group">
            <input type="text" id="search-input" placeholder="Search senders..." />
        </div>
        <div class="input-group">
            <label>显示Sender数量:</label>
            <input type="number" id="num-senders-input" value="10" min="1" max="100" style="padding: 4px; border: 1px solid var(--color-border); border-radius: 4px;"/>
        </div>
        <div class="input-group">
            <label>Sort by:</label>
            <select id="sort-method-select">
                <option value="node_count">By Tree Node Count</option>
                <option value="recent_time">By Newest Time</option>
            </select>
        </div>
        <div class="input-group">
            <label>Min Trees Length (show trees with max depth >= this value):</label>
            <select id="min-tree-len-select">
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3" selected>3</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="6">6</option>
                <option value="7">7</option>
                <option value="8">8</option>
                <option value="9">9</option>
                <option value="10">10</option>
            </select>
        </div>
        <div id="sender-list"></div>
    </div>

    <div id="main-content">
        <div id="toolbar">
            <label style="font-size: 14px; font-weight: 500;">Layout Direction: </label>
            <select id="layout-toggle">
                <option value="LR">Left to Right (LR)</option>
                <option value="TB">Top to Bottom (TB)</option>
            </select>
            <button id="reset-zoom">Reset/Center</button>
        </div>
        <div id="tree-container"></div>
    </div>

    <!-- 弹窗结构 -->
    <div id="emailModal" class="modal">
      <div class="modal-content">
        <span class="close" onclick="document.getElementById('emailModal').style.display='none'">&times;</span>
        <h3 id="modal-title">Sender - Subject</h3>
        <p class="modal-field" id="modal-time">Time: </p>
        <p class="modal-field" id="modal-to">To: </p>
        <p class="modal-field" id="modal-cc" style="margin-bottom: 15px;">Cc: </p>
        <hr>
        <div id="modal-body" class="modal-body">Email Body...</div>
      </div>
    </div>

    <script>
// [[INJECT_TREE_LOGIC]]
    </script>
</body>
</html>
"""
        
        # Inject external JS
        project_root = os.path.dirname(os.path.dirname(__file__))
        js_path = os.path.join(project_root, "frontend", "tree_logic.js")
        js_content = ""
        if os.path.exists(js_path):
            with open(js_path, "r", encoding="utf-8") as js_file:
                js_content = js_file.read()
        
        # Uniformly replace data and JS logic        
        # 因为 tree_logic.js 第一行是 `const treeData = __JSON_DATA__;`，所以直接替换 __JSON_DATA__
        js_content = js_content.replace("__JSON_DATA__", json_data)
        html_content = html_template.replace("// [[INJECT_TREE_LOGIC]]", js_content)

        out_path = os.path.join(self.output_dir, filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return out_path