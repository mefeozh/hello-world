import re
import yaml

content = open('/Users/hikmatgasimzade/Desktop/is_guc/odtusat/website/uye-listesi.html').read()
rows = re.findall(r'<tr>\s*<td>\s*(\d+)\s*</td>\s*<td>\s*([^<]+?)\s*</td>\s*<td>\s*([^<]+?)\s*</td>\s*</tr>', content, re.DOTALL)

members = []
for row in rows:
    members.append({
        'number': int(row[0]),
        'name': row[1].strip(),
        'year': row[2].strip()
    })

with open('/Users/hikmatgasimzade/Desktop/is_guc/odtusat/new_version/data/members.yaml', 'w', encoding='utf-8') as f:
    yaml.dump({'members': members}, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

print(f"Parsed {len(members)} members into data/members.yaml.")
