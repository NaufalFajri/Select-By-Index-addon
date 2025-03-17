import bpy
import bmesh

class SelectByIndex(bpy.types.Operator):
    """Select all vertices, edges, or faces within an index range"""
    bl_idname = "select.select_by_index"
    bl_label = "Select By Index"
    bl_options = {'REGISTER', 'UNDO'}

    def update_start(self, context):
        if self.start > self.stop:
            self.stop = self.start
    
    def update_stop(self, context):
        if self.stop < self.start:
            self.start = self.stop

    select_mode: bpy.props.EnumProperty(
        name="Selection Mode",
        description="Choose a selection mode",
        items=[
            ('VERTEX', "Vertex", "Select vertices"),
            ('EDGE', "Edge", "Select edges"),
            ('FACE', "Face", "Select faces"),
        ]
    )

    start: bpy.props.IntProperty(
        name="Selection Start",
        description="The starting index for the selection range",
        default=0,
        min=0,
        update=update_start
    )
    
    stop: bpy.props.IntProperty(
        name="Selection Stop",
        description="The ending index for the selection range (inclusive)",
        default=0,
        min=0,
        update=update_stop
    )

    def check(self, context):
        obj = context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        max_index = 0

        if self.select_mode == 'VERTEX':
            max_index = len(bm.verts)-1
        elif self.select_mode == 'EDGE':
            max_index = len(bm.edges)-1
        elif self.select_mode == 'FACE':
            max_index = len(bm.faces)-1

        if self.start > max_index or self.stop > max_index:
            self.start = min(self.start, max_index)
            self.stop = min(self.stop, max_index)
            return True
        return False

    def execute(self, context):
        obj = context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        if self.select_mode == 'VERTEX':
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            for vert in bm.verts:
                if vert.index >= self.start and vert.index <= self.stop:
                    vert.select = True
                else:
                    vert.select = False
        elif self.select_mode == 'EDGE':
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            for edge in bm.edges:
                if edge.index >= self.start and edge.index <= self.stop:
                    edge.select = True
                else:
                    edge.select = False
        elif self.select_mode == 'FACE':
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            for face in bm.faces:
                if face.index >= self.start and face.index <= self.stop:
                    face.select = True
                else:
                    face.select = False

        bm.select_flush_mode()
        bmesh.update_edit_mesh(me)
        return {'FINISHED'}
        
    def invoke(self, context, event):
        obj = context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        if context.tool_settings.mesh_select_mode[0]:  # Vertex mode
            self.select_mode = 'VERTEX'
        elif context.tool_settings.mesh_select_mode[1]:  # Edge mode
            self.select_mode = 'EDGE'
        elif context.tool_settings.mesh_select_mode[2]:  # Face mode
            self.select_mode = 'FACE'

        self.check(context)
        
        return self.execute(context)

def menu_func(self, context):
    self.layout.operator(SelectByIndex.bl_idname, text="By Index")

def register():
    bpy.utils.register_class(SelectByIndex)
    bpy.types.VIEW3D_MT_select_edit_mesh.append(menu_func)

def unregister():
    bpy.utils.unregister_class(SelectByIndex)
    bpy.types.VIEW3D_MT_select_edit_mesh.remove(menu_func)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()