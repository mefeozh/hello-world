import re

with open('data/members.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

entries = []
blocks = re.split(r'\n  - ', content.strip())
blocks[0] = re.sub(r'^members:\n  - ', '', blocks[0])

for block in blocks:
    lines = block.strip().split('\n')
    entry = {}
    for line in lines:
        m = re.match(r"    (\w+): (.+)", line)
        if m:
            key, val = m.group(1), m.group(2).strip("'")
            entry[key] = val
    if entry:
        entries.append(entry)

def sort_key(e):
    year = int(e.get('year', 9999))
    number = int(e['number']) if 'number' in e else float('inf')
    return (year, number)

entries.sort(key=sort_key)

out = ['members:']
for e in entries:
    if 'number' in e:
        out.append(f"  - number: {e['number']}")
        out.append(f"    name: {e['name']}")
        out.append(f"    year: '{e['year']}'")
    else:
        out.append(f"  - name: {e['name']}")
        out.append(f"    year: '{e['year']}'")

with open('data/members.yaml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out) + '\n')

print(f"Sorted {len(entries)} members by year then number")
