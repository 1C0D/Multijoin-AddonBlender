import bpy
import bmesh
from bpy.types import Menu

'''
-Press J to join
-Press J and move to enter pie menu:
    -multijoin need a last selected vertex
    -slide and join need 2 last vert or 1 last edge
'''    


bl_info = {
    "name": "Multijoin_Pie_Menu",
    "author": "1C0D",
    "version": (1, 2, 5),
    "blender": (2, 83, 0),
    "location": "View3D",
    "description": "Normal Join, Multijoin at last, slide and join",
    "category": "Mesh",
}

class SLIDE_OT_JOIN(bpy.types.Operator):
    """Slide and Join"""
    bl_idname = "join.slide"
    bl_label = "Slide and Join"
    bl_options = {"UNDO","REGISTER"}  

    def execute(self, context): 

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()         
        obj=bpy.context.object

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        
        sel=[v.index for v in bm.verts if v.select]  
        sel_count = len(sel)   

        if sel_count>3:
            try:
                v0=bm.select_history[-1]
                v1=bm.select_history[-2] #2last verts
                if not isinstance(v0, bmesh.types.BMVert):
                    raise IndexError
                if not isinstance(v1, bmesh.types.BMVert):
                    raise IndexError
                
            except IndexError:
                self.report({'WARNING'}, "Need 2 last vertices")
                return {'CANCELLED'} 
 
            
            v0id=v0.index  #after subdiv index will be needed because history changed
            v1id=v1.index
            
            vertlist = []               #all vert selected except 2 last one
            vertlistid=[]
            
            bm.verts.ensure_lookup_table()
            for v in bm.verts:
                if v.select and v != v0 and v != v1:
                    vertlist.append(v) 
                    vertlistid.append(v.index)        

########################################find extrem in vertlist     
  
            v2count=[]
            for v in vertlist:
                v2 = None
                for e in v.link_edges:
                    v2 = e.other_vert(v)
                    if v2 in vertlist:
                        v2count.append(v2)
            extremcount=[]
            extremcountid=[]
            for v in v2count:
                count=v2count.count(v)
                if count<2:
                    extremcount.append(v)
                    extremcountid.append(v.index)
            
            E0id,E1id=extremcountid[:]
            
########################################add/split/delete up face
           
            bmesh.ops.connect_verts(bm, verts=[v0, v1])

            try:
                bm.edges.new([v1, v0])
            except:
                pass
                
            for v in vertlist:   #if no face create it
                v2 = None
                for e in v.link_edges:
                    v2 = e.other_vert(v)
                    if v2 in vertlist:                        
                        for f in v0.link_faces:
                            if v in f.verts and v2 in f.verts:
                                break   
                            else:
                                bpy.ops.mesh.edge_face_add()
            

            for v in vertlist: 
                for f in v0.link_faces:
                    if v1 in f.verts and v in f.verts:
                        f.select=True
                        break   
                    
            faces = [f for f in bm.faces if f.select]
            bmesh.ops.delete(bm, geom=faces, context= 'FACES_ONLY')      
          
########################################edges between create                   
                        
            E0,E1=extremcount[:]           
            if (E0.co - v0.co).length <= (E0.co - v1.co).length:
                try:
                    bmesh.ops.connect_verts(bm, verts=[E0, v0])    
                except:# ValueError:
                    bm.edges.new([E0, v0])
                try:
                    bmesh.ops.connect_verts(bm, verts=[E1, v1])    
                except:# ValueError:
                    bm.edges.new([E1, v1])
            else:
                try:
                    bmesh.ops.connect_verts(bm, verts=[E0, v1]) 
                        
                except:# ValueError:
                    bm.edges.new([E0, v1])
                try:
                    bmesh.ops.connect_verts(bm, verts=[E1, v0])    
                except:# ValueError:
                    bm.edges.new([E1, v0])

##################################################subdiv and get new verts
            
            for v in bm.verts:
                v.select = False
            v0.select=True                #select edge v0v1
            v1.select=True     
            bm.select_flush_mode()                   
                      
            edges = [e for e in bm.edges if e.select] 
            newmesh=bmesh.ops.subdivide_edges(bm, edges=edges, cuts=sel_count-4)

                         
            newid=[]    #get id new vertices
            
            bm.edges.ensure_lookup_table()
            
            for i in newmesh['geom_split']:
                if type(i) == bmesh.types.BMVert:
                    newid.append(i.index) 
                                                  
#################################################### Add faces

            bm.verts.ensure_lookup_table()
            allvertid=sel
            allvertid.extend(newid)
            
            for i in allvertid:
                bm.verts[i].select=True
                    
            bm.select_flush_mode()

            v0=bm.verts[v0id]
            v1=bm.verts[v1id] 
            
            bm.edges.ensure_lookup_table()
            
            v2 = None 
            for e in v0.link_edges:
                v2 = e.other_vert(v0)
                if v2.index==E0id or v2.index==E1id:   #adjacente edge linked to v0... before F
                    e.select=False
                    break  
            
            v2 = None 
            for e in v1.link_edges:
                v2 = e.other_vert(v1)
                if v2.index==E0id or v2.index==E1id:   #adjacente edge linked to v0... before F
                    e.select=False
                    break                  
                      
            edges1 = [e for e in bm.edges if e.select]  
            

            try:    
                bpy.ops.mesh.bridge_edge_loops()
                # bmesh.ops.grid_fill(bm, edges=edges1)
            except:
                 self.report({'WARNING'}, "Need 2 edges loops")    
#####################################################Next selection
            
            bm.verts.ensure_lookup_table() 

            v0=bm.verts[v0id]
            v1=bm.verts[v1id]
                
            bpy.ops.mesh.select_all(action='DESELECT')    
   
            v0.select=True
            v1.select=True 
            for i in newid:
                bm.verts[i].select=True #ok 
            
            context.tool_settings.mesh_select_mode=(True,False,False)  
                     
            bm.verts.ensure_lookup_table()                

            v2=None
            othervertid=[]
            othervert=[]
            next=[]
            for e in v0.link_edges:
                v2 = e.other_vert(v0)

                if v2.index in vertlistid:
                    continue
                if v2.index in newid:
                    continue
                if v2==v1:
                    continue                
                else:
                    next.append(v2)
                    
            v3=None
            for e in v1.link_edges:
                v3 = e.other_vert(v1)

                if v3.index in vertlistid:
                    continue
                if v3.index in newid:
                    continue
                if v3==v0:
                    continue                
                else:
                    next.append(v3)

            for v in next:            
                if v.index in newid:
                    continue
                if v.index  in vertlistid:
                    continue                 
                for f in v.link_faces:
                    if not v0 in f.verts:
                        continue
                    if not v1 in f.verts:
                        continue
                    else:
                        v.select=True
                        bm.select_history.add(v)    
        
            bmesh.update_edit_mesh(obj.data)
        
            
            return {'FINISHED'}
        
        else:
            self.report({'WARNING'}, "select more vertices") 
            return {'CANCELLED'}
    

class MULTI_OT_JOIN1(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "multi.join"
    bl_label = "Multijoin"
    bl_options = {"UNDO"}

    def execute(self, context):
        
        obj=bpy.context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        actvert=bm.select_history.active        
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
            bm.free()
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()               

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
    kc = wm.keyconfigs.addon
    if kc.keymaps.get("Mesh", None):
        for k in kc.keymaps["Mesh"].keymap_items:
            if k.idname == "mesh.vert_connect_path" and k.active:
                k.value = 'CLICK'

    if kc:
        km = kc.keymaps.new(name = 'Mesh')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'J', 'CLICK_DRAG')
        kmi.properties.name = "MULTIJOIN_MT_MENU"
        addon_keymaps.append((km, kmi))

def key_back():

    wm = bpy.context.window_manager   
    kc = wm.keyconfigs.addon
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
        

    

        
