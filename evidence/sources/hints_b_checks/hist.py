import subprocess, re, json, sys
repo='/home/user/test/data/raw/magnus'
commits=subprocess.run(['git','-C',repo,'log','--reverse','--format=%h|%ad|%s','--date=iso','--','src/data/innhold.ts'],capture_output=True,text=True).stdout.strip().split('\n')
def parse(src):
    m=re.search(r'export const HINT[^=]*=\s*\[\n(.*?)\n\]\n',src,re.S)
    if not m: return None
    body=m.group(1)
    entries={}
    order=[]
    cur=None
    for line in body.split('\n'):
        if re.match(r'^  \{\s*$',line):
            cur={}
        elif re.match(r'^  \},?\s*$',line):
            if cur is not None and 'id' in cur:
                entries[cur['id']]=cur; order.append(cur['id'])
            cur=None
        elif cur is not None:
            mm=re.match(r'^    (\w+):\s*(.*?),?\s*$',line)
            if mm:
                k,v=mm.group(1),mm.group(2)
                if k=='id': v=v.strip("'")
                cur[k]=v
            else:
                cur.setdefault('_extra',[]).append(line)
        else:
            # single-line entry?
            mm=re.match(r"^  \{ id: '([^']+)'",line)
            if mm: entries[mm.group(1)]={'id':mm.group(1),'raw':line}; order.append(mm.group(1))
    return entries,order
prev={}
out=[]
for c in commits:
    h,d,s=c.split('|',2)
    src=subprocess.run(['git','-C',repo,'show',f'{h}:src/data/innhold.ts'],capture_output=True,text=True).stdout
    r=parse(src)
    if r is None:
        continue
    ents,order=r
    for i in ents:
        if i not in prev:
            out.append(f'[{h} {d} | {s}] ADDED {i}: ' + json.dumps(ents[i],ensure_ascii=False))
        else:
            for k in set(ents[i])|set(prev[i]):
                if ents[i].get(k)!=prev[i].get(k):
                    out.append(f'[{h} {d} | {s}] CHANGED {i}.{k}:\n   OLD: {prev[i].get(k)}\n   NEW: {ents[i].get(k)}')
    for i in prev:
        if i not in ents:
            out.append(f'[{h} {d} | {s}] REMOVED {i}: ' + json.dumps(prev[i],ensure_ascii=False))
    prev=ents
print('\n'.join(out))
