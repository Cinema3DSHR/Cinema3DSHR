import bpy, sys, time
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
sc = bpy.context.scene
for f in [int(x) for x in a[2].split(',')]:
    sc.frame_set(f)
    sc.render.filepath = f'{a[1]}_{f:05d}.png'
    t = time.time(); bpy.ops.render.render(write_still=True)
    print('RENDER', f, round(time.time() - t, 1), 's', sc.camera.name if sc.camera else None, flush=True)
