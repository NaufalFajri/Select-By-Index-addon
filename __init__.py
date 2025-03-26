import bpy
import bmesh

class SelectByIndex(bpy.types.Operator):
    """Select all vertices, edges, or faces within an index range"""
    bl_idname = "mesh.select_by_index"
    bl_label = "Select By Index"
    bl_options = {'REGISTER', 'UNDO'}

    # Increment stop when user increments start above stop
    def update_start(self, context):
        min_stop = self.start if self.inc_stop_index else self.start + 1
        if self.stop < min_stop:
            self.stop = min_stop
    
    # Decrement start when user decrements stop below start
    def update_stop(self, context):
        max_start = self.stop if self.inc_stop_index else max(self.stop - 1, 0)
        if self.start > max_start:
            self.start = max_start

    # Increment or Decrement stop index when changing selection range inclusivity
    def update_inc_stop_index(self, context):
        self.stop = max(self.stop - 1, 0) if self.inc_stop_index else self.stop + 1

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
        description="The ending index for the selection range",
        default=0,
        min=0,
        update=update_stop
    )

    replace_selection: bpy.props.BoolProperty(
        name="Replace Selection",
        description="Replace instead of adding to the previous selection",
        default=True
    )

    inc_stop_index: bpy.props.BoolProperty(
        name="Inclusive Stop Index",
        description="Make the ending index for the selection range inclusive",
        default=True,
        update=update_inc_stop_index
    )

    @classmethod
    def poll(cls, context):
        if context.object.mode == 'EDIT':
            return True
        cls.poll_message_set("The active object must be in Edit mode")
        return False

    def check(self, context):
        bm = bmesh.from_edit_mesh(context.object.data)

        if self.select_mode == 'VERTEX':
            max_stop = len(bm.verts)
        elif self.select_mode == 'EDGE':
            max_stop = len(bm.edges)
        elif self.select_mode == 'FACE':
            max_stop = len(bm.faces)

        bm.free()

        max_start = max(max_stop - 1, 0)
        
        if self.inc_stop_index:
            max_stop = max_start

        if self.start > max_start or self.stop > max_stop:
            self.start = min(self.start, max_start)
            self.stop = min(self.stop, max_stop)
            return True
        
        if not self.inc_stop_index and max_stop > 0 and self.stop < 1:
            self.stop = 1
            return True

        return False

    def execute(self, context):
        if self.replace_selection:
            bpy.ops.mesh.select_all(action='DESELECT')

        me = context.object.data
        bm = bmesh.from_edit_mesh(me)

        if self.select_mode == 'VERTEX':
            bpy.ops.mesh.select_mode(type='VERT')
            selectable_items = bm.verts
        elif self.select_mode == 'EDGE':
            bpy.ops.mesh.select_mode(type='EDGE')
            selectable_items = bm.edges
        elif self.select_mode == 'FACE':
            bpy.ops.mesh.select_mode(type='FACE')
            selectable_items = bm.faces

        start = self.start
        stop = self.stop + 1 if self.inc_stop_index else self.stop
        
        for index, item in enumerate(selectable_items):
            if index >= start and index < stop:
                item.select = True
        
        bm.select_flush_mode()
        bm.free()
        bmesh.update_edit_mesh(me)
        return {'FINISHED'}
        
    def invoke(self, context, event):
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
    bpy.types.VIEW3D_MT_select_edit_mesh.remove(menu_func)
    bpy.utils.unregister_class(SelectByIndex)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()