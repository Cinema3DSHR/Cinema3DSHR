import json, struct, sys
src, dst = sys.argv[1], sys.argv[2]
d = open(src,'rb').read(); _,_,ln = struct.unpack('<4sII', d[:12]); off=12; chunks=[]
while off < ln:
    cl, ct = struct.unpack('<II', d[off:off+8]); chunks.append([ct, d[off+8:off+8+cl]]); off += 8+cl
js = json.loads(chunks[0][1])
ocultos=[]
for i,n in enumerate(js['nodes']):
    e = n.get('extensions',{})
    if 'KHR_node_visibility' in e:
        if e['KHR_node_visibility'].get('visible') is False: ocultos.append(n.get('name'))
        del e['KHR_node_visibility']
        if not e: del n['extensions']
for k in ('extensionsUsed','extensionsRequired'):
    if k in js:
        js[k]=[x for x in js[k] if x!='KHR_node_visibility']
        if not js[k]: del js[k]
print('ocultos:',ocultos)
j = json.dumps(js, separators=(',',':')).encode(); j += b' '*((4-len(j)%4)%4); chunks[0][1]=j
out = b''.join(struct.pack('<II',len(c),t)+c for t,c in chunks)
open(dst,'wb').write(struct.pack('<4sII',b'glTF',2,12+len(out))+out)
