import urllib.request
import json
import base64
import os
import webbrowser
import getpass
from datetime import datetime

# Load environment variables from .env file if it exists
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key.strip()] = value.strip()

API_KEY = os.environ.get("PAGECLIP_API_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

if not API_KEY:
    print("Error: PAGECLIP_API_KEY not found. Please add it to your .env file.")
    exit(1)

print("--- Secure Orders Dashboard ---")
pwd = getpass.getpass("Enter Admin Password: ")
if pwd != ADMIN_PASSWORD:
    print("Access Denied! Incorrect password.")
    exit(1)

URL = "https://api.pageclip.co/api/data/chicken_order"

auth_string = f"{API_KEY}:"
base64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')

req = urllib.request.Request(URL)
req.add_header("Authorization", f"Basic {base64_auth}")

try:
    print("Fetching orders from Pageclip...")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
except Exception as e:
    print(f"Failed to fetch data: {e}")
    exit(1)

table_content = """
    <h1>Chicken Delivery Orders</h1>
    <p class="subtitle">Latest submissions from your Pageclip form</p>
    <table>
        <tr>
            <th>Date</th>
            <th>Customer Name</th>
            <th>Phone</th>
            <th>Email</th>
            <th>Location</th>
            <th>Qty</th>
            <th>Total (Ksh)</th>
            <th>Notes</th>
        </tr>
"""

items = data.get("data", [])
if not items:
    table_content += "<tr><td colspan='8' class='empty'>No orders found yet. Submit a test order on your website first!</td></tr>\n"
else:
    for item in items:
        # Parse date and format it
        try:
            dt = datetime.strptime(item.get("createdAt", ""), "%Y-%m-%dT%H:%M:%SZ")
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = item.get("createdAt", "")
            
        payload = item.get("payload", {})
        
        name = f"{payload.get('first_name', '')} {payload.get('last_name', '')}".strip()
        phone = payload.get('phone_number', '')
        email = payload.get('email', '')
        
        addr = payload.get('street_address', '')
        city = payload.get('city', '')
        apt = payload.get('apartment', '')
        
        location = f"{addr}, {city}"
        if apt:
            location += f" ({apt})"
            
        qty = payload.get('chicken_quantity', '')
        price = payload.get('total_price', '')
        notes = payload.get('order_notes', '')

        table_content += f"""
        <tr>
            <td>{date_str}</td>
            <td>{name}</td>
            <td>{phone}</td>
            <td>{email}</td>
            <td>{location}</td>
            <td>{qty}</td>
            <td>{price}</td>
            <td>{notes}</td>
        </tr>
        """

table_content += """
    </table>
"""

# Encrypt the table_content using RC4 so it's not plaintext in HTML
def rc4_encrypt(key, data):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) % 256
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for char in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        out.append(char ^ S[(S[i] + S[j]) % 256])
    return base64.b64encode(out).decode('ascii')

plain_text = "MAGIC:" + table_content
encrypted_b64 = rc4_encrypt(ADMIN_PASSWORD.encode('utf-8'), plain_text.encode('utf-8'))

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chicken Delivery Orders</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background-color: #f9f9f9; color: #333; }}
        h1 {{ color: #d32f2f; margin-bottom: 5px; }}
        p.subtitle {{ color: #555; margin-top: 0; margin-bottom: 20px; }}
        table {{ border-collapse: collapse; width: 100%; background-color: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #fbfbfb; }}
        .empty {{ font-style: italic; color: #777; text-align: center; padding: 20px; }}
    </style>
</head>
<body>
    <div id="content"></div>
    <script>
        function rc4_decrypt(key, b64data) {{
            var data = atob(b64data);
            var s = [], j = 0, x, res = '';
            for (var i = 0; i < 256; i++) {{
                s[i] = i;
            }}
            for (i = 0; i < 256; i++) {{
                j = (j + s[i] + key.charCodeAt(i % key.length)) % 256;
                x = s[i];
                s[i] = s[j];
                s[j] = x;
            }}
            i = 0;
            j = 0;
            for (var y = 0; y < data.length; y++) {{
                i = (i + 1) % 256;
                j = (j + s[i]) % 256;
                x = s[i];
                s[i] = s[j];
                s[j] = x;
                res += String.fromCharCode(data.charCodeAt(y) ^ s[(s[i] + s[j]) % 256]);
            }}
            return decodeURIComponent(escape(res));
        }}

        var encryptedData = "{encrypted_b64}";
        var pass = prompt("Please enter the admin password to view the orders:");
        if (pass) {{
            try {{
                var decrypted = rc4_decrypt(pass, encryptedData);
                if (decrypted.startsWith("MAGIC:")) {{
                    document.getElementById('content').innerHTML = decrypted.substring(6);
                }} else {{
                    document.body.innerHTML = "<h1 style='text-align:center; padding: 50px; color: #d32f2f; font-family: sans-serif;'>Access Denied! Incorrect Password.</h1>";
                }}
            }} catch(e) {{
                document.body.innerHTML = "<h1 style='text-align:center; padding: 50px; color: #d32f2f; font-family: sans-serif;'>Access Denied! Incorrect Password.</h1>";
            }}
        }} else {{
            document.body.innerHTML = "<h1 style='text-align:center; padding: 50px; color: #d32f2f; font-family: sans-serif;'>Access Denied!</h1>";
        }}
    </script>
</body>
</html>"""

html_path = os.path.abspath("orders.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generated {html_path}")
print("Opening in browser...")
webbrowser.open(f"file://{html_path}")
