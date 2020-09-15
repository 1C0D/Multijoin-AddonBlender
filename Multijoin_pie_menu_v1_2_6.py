import bpy
import bmesh
from bpy.types import Menu
from bpy.props import FloatProperty, BoolProperty

'''
-Press J to join
-Press J and move to enter pie menu:
    -multijoin need a last selected vertex
    -slide and join need 2 last vert or 1 last edge
'''


bl_info = {
    "name": "Multijoin_Pie_Menu",
    "author": "1C0D",
    "version": (1, 2, 6),
    "blender": (2, 83, 0),
    "location": "View3D",
    "description": "Normal Join, Multijoin at last, slide and join",
    "category": "Mesh",
}


class SLIDE_OT_JOIN(bpy.types.Operator):
    """Slide and Join"""
    bl_idname = "join.slide"
    bl_label = "Slide and Join"
    bl_options = {"UNDO", "REGISTER"}

    rmv_doubles_threshold: FloatProperty(
        name="Threshold", default=0.0001, precision=4, step=0.004, min=0)

    def execute(self, context):

        obj = bpy.context.active_object
        bm = bmesh.from_edit_mesh(obj.data)
        bm.normal_update()

        bm.verts.ensure_lookup_table()
        history = bm.select_history[:]

        sel = [v.index for v in bm.verts if v.select]
        sel_count = len(sel)

        if sel_count > 3:
            try:
                V0 = history[-1]
                V1 = history[-2]  # 2last verts
                if not isinstance(V0, bmesh.types.BMVert):
                    raise IndexError
                if not isinstance(V1, bmesh.types.BMVert):
                    raise IndexError

            except IndexError:
                self.report({'WARNING'}, "Need 2 last vertices")
                return {'CANCELLED'}

            v0id = V0.index  # after subdiv index will be needed because history changed
            v1id = V1.index

            vertlist = []  # all vert selected except 2 last one
            vertlistid = []

            bm.verts.ensure_lookup_table()

            vertlist = [v for v in bm.verts
                        if (v.select and v != V0 and v != V1)]
            vertlist = vertlist[:]

# find extrem in vertlist

            v_double_count = [v for v in vertlist
                              for e in v.link_edges if e.other_vert(v) in vertlist]
            extremcount = [(v.index, v)
                           for v in v_double_count if v_double_count.count(v) < 2]
            try:
                E0, E1 = extremcount[:]
            except ValueError:
                self.report({'WARNING'}, "Invalid selection")
                return {'CANCELLED'}


# connect V0V1 if not

            bmesh.ops.connect_verts(bm, verts=[V0, V1])

            try:
                bm.edges.new([V1, V0])
            except:
                pass

# delete faces to have no doubles after

            for v in vertlist:
                for f in V0.link_faces:
                    if V1 in f.verts and v in f.verts:
                        f.select = True
                        break

            faces = [f for f in bm.faces if f.select]
            bmesh.ops.delete(bm, geom=faces, context='FACES_ONLY')

# connect extrems and V0 V1 if not

            if (E0[1].co - V0.co).length <= (E0[1].co - V1.co).length:

                bmesh.ops.connect_verts(bm, verts=[E0[1], V0])
                try:
                    bm.edges.new([E0[1], V0])
                except:  # ValueError:
                    pass
                bmesh.ops.connect_verts(bm, verts=[E1[1], V1])
                try:
                    bm.edges.new([E1[1], V1])
                except:
                    pass
            else:
                bmesh.ops.connect_verts(bm, verts=[E0[1], V1])
                try:
                    bm.edges.new([E0[1], V1])
                except:
                    pass
                bmesh.ops.connect_verts(bm, verts=[E1[1], V0])
                try:
                    bm.edges.new([E1[1], V0])
                except:
                    pass

# subdiv and get new verts

            for v in bm.verts:
                v.select = False
            V0.select = True  # select edge v0v1
            V1.select = True
            bm.select_flush_mode()

            edges = [e for e in bm.edges if e.select]
            newmesh = bmesh.ops.subdivide_edges(
                bm, edges=edges, cuts=sel_count-4)

            newid = []  # get id new vertices

            bm.verts.ensure_lookup_table()

            for i in newmesh['geom_split']:
                if type(i) == bmesh.types.BMVert:
                    newid.append(i.index)

# Add faces

            bm.verts.ensure_lookup_table()
            allvertid = sel+newid

            for i in allvertid:
                bm.verts[i].select = True

            bm.select_flush_mode()

            V0 = bm.verts[v0id]
            V1 = bm.verts[v1id]

            bm.edges.ensure_lookup_table()

            v2 = None
            for e in V0.link_edges:  # deselect adjacent edges
                v2 = e.other_vert(V0)
                if v2.index == E0[0] or v2.index == E1[0]:
                    e.select = False
                    break

            v2 = None
            for e in V1.link_edges:
                v2 = e.other_vert(V1)
                if v2.index == E0[0] or v2.index == E1[0]:
                    e.select = False
                    break

            edges1 = [e for e in bm.edges if e.select]
            print("edges1", len(edges1))

            try:
                bmesh.ops.bridge_loops(bm, edges=edges1)  # bridge loops

            except RuntimeError:
                self.report({'WARNING'}, "Need 2 edges loops")
                return {'CANCELLED'}
# Next selection

            bpy.ops.mesh.select_all(action='DESELECT')

            V0.select = True
            V1.select = True
            for i in newid:
                bm.verts[i].select = True  # ok

            bm.verts.ensure_lookup_table()

            v2 = None
            othervertid = []
            othervert = []
            next = []
#            bm.verts.ensure_lookup_table()
            for e in V0.link_edges:
                v2 = e.other_vert(V0)

                if v2.index in vertlist:
                    continue
                if v2.index in newid:
                    continue
                if v2 == V1:
                    continue
                else:
                    next.append(v2)

            v3 = None
            for e in V1.link_edges:
                v3 = e.other_vert(V1)

                if v3.index in vertlist:
                    continue
                if v3.index in newid:
                    continue
                if v3 == V0:
                    continue
                else:
                    next.append(v3)

            for v in next:
                if v.index in newid:
                    continue
                if v.index in vertlist:
                    continue
                for f in v.link_faces:
                    if not V0 in f.verts:
                        continue
                    if not V1 in f.verts:
                        continue
                    else:
                        v.select = True
                        bm.select_history.add(v)

            bmesh.ops.remove_doubles(
                bm, verts=bm.verts, dist=self.rmv_doubles_threshold)
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)
            bmesh.update_edit_mesh(obj.data)
            print('mabelleconscienceq')

            return {'FINISHED'}

        else:
            self.report({'WARNING'}, "select more vertices")
            return {'CANCELLED'}


class MULTI_OT_JOIN1(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "multi.join"
    bl_label = "Multijoin"
    bl_options = {"UNDO"}

    def execute(self, context):  # "selected objects"

        obj = bpy.context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.normal_update()
        bm.verts.ensure_lookup_table()
        actvert = bm.select_history.active
        if (isinstance(actvert, bmesh.types.BMVert)):
            vertlist = []
            for v in bm.verts:
                if v.select:
                    if not(v == actvert):
                        vertlist.append(v)

            # do connection
            for v in vertlist:
                for f in actvert.link_faces:
                    if v in f.verts:
                        # when already face: split it
                        bmesh.ops.connect_verts(bm, verts=[v, actvert])

            for v in vertlist:
                v2 = None
                for e in v.link_edges:
                    v2 = e.other_vert(v)
                    if v2 in vertlist:
                        already = False
                        for f in actvert.link_faces:
                            if v in f.verts and v2 in f.verts:
                                already = True
                                break
                        # if no face already between to first and selected vert: make it
                        if not(already):
                            bm.faces.new([v, actvert, v2])

            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=0.0001)

            face_sel = [f for f in bm.faces if f.select]
            bmesh.ops.recalc_face_normals(bm, faces=face_sel)

            bmesh.update_edit_mesh(me)

        else:

            self.report({'WARNING'}, "No last selected vertex")

        return {'CANCELLED'}


class MULTIJOIN_MT_MENU (Menu):
    bl_label = ""

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        pie.operator("multi.join", text="Multi Join")
        pie.operator("join.slide", text="Slide and Join")
        pie.operator("mesh.vert_connect", text="Connect vert pairs")


addon_keymaps = []


def modify_key():

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.user
    for k in kc.keymaps["Mesh"].keymap_items:
        if k.idname == "mesh.vert_connect_path" and k.active:
            k.value = 'CLICK'

    if kc:
        km = kc.keymaps.new(name='Mesh')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'J', 'CLICK_DRAG')
        kmi.properties.name = "MULTIJOIN_MT_MENU"
        addon_keymaps.append((km, kmi))


def key_back():

    wm = bpy.context.window_manager   
    kc = wm.keyconfigs.user
    for k in kc.keymaps["Mesh"].keymap_items:
        if k.idname == "mesh.vert_connect_path" and k.active:
            k.value = 'PRESS'
            
    for km, kmi in addon_keymaps:
        if hasattr(kmi.properties, 'name'):
            if kmi.properties.name == "MULTIJOIN_MT_MENU":
                km.keymap_items.remove(kmi)
                    
    addon_keymaps.clear()


classes = (SLIDE_OT_JOIN, MULTI_OT_JOIN1, MULTIJOIN_MT_MENU)


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    modify_key()


def unregister():

    key_back()

    for cls in classes:
        bpy.utils.unregister_class(cls)
