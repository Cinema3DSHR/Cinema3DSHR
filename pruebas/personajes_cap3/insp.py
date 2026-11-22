import bpy, sys, json
ruta=sys.argv[sys.argv.index('--')+1]
if ruta.endswith('.fbx'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta)
else:
    bpy.ops.wm.open_mainfile(filepath=ruta)
print('ARCHIVO',ruta)
print('ESCENAS',[s.name for s in bpy.data.scenes],'OBJ',len(bpy.data.objects),'COL',[c.name for c in bpy.data.collections][:20])
tot=0
for o in bpy.data.objects:
    if o.type=='MESH':
        me=o.data
        tris=sum(len(p.vertices)-2 for p in me.polygons)
        tot+=tris
        sk=me.shape_keys
        nsk=len(sk.key_blocks) if sk else 0
        print('MESH',o.name,'v',len(me.vertices),'tris',tris,'mats',[m.name for m in me.materials if m],'uv',[u.name for u in me.uv_layers],'sk',nsk,'vg',len(o.vertex_groups),'mod',[m.type for m in o.modifiers],'parent',o.parent.name if o.parent else None, 'hide',o.hide_viewport,o.hide_render)
        if nsk: print('   SKEYS',[k.name for k in sk.key_blocks][:80])
    elif o.type=='ARMATURE':
        print('ARM',o.name,'bones',len(o.data.bones),'parent',o.parent.name if o.parent else None)
        print('   BONES',[b.name for b in o.data.bones][:140])
    elif o.type not in ('MESH',):
        print('OTRO',o.name,o.type)
print('TRIS_TOTAL',tot)
print('ACCIONES',[(a.name,[round(x) for x in a.frame_range]) for a in bpy.data.actions][:30])
print('IMAGENES',[(i.name,i.size[:],bool(i.packed_file),i.filepath[:60]) for i in bpy.data.images][:40])
print('MATERIALES',len(bpy.data.materials),[m.name for m in bpy.data.materials][:40])
print('SHAPEKEYS_DATA',[(k.name,len(k.key_blocks)) for k in bpy.data.shape_keys])
