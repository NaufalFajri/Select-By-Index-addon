bl_info = {
    "name": "Select By Index (Range)",
    "author": "Adapted from EricBanker12",
    "version": (1, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Select > By Index",
    "description": "Select vertices / edges / faces by specifying start and end (or count)",
    "warning": "",
    "wiki_url": "",
    "category": "Mesh",
}

import bpy
import bmesh
from itertools import islice

class SelectByIndex(bpy.types.Operator):
    """Select all vertices, edges, or faces within an index range"""
    bl_idname = "mesh.select_by_index"
    bl_label = "Select By Index"
    bl_options = {'REGISTER', 'UNDO'}
    
    select_mode: bpy.props.EnumProperty(
        name="Select Mode",
        description="Choose a selection mode",
        items=[
            ('VERTEX', "Vertex", "Select vertices"),
            ('EDGE',   "Edge",   "Select edges"),
            ('FACE',   "Face",   "Select faces"),
        ],
    )
    input_mode: bpy.props.EnumProperty(
        name="Input Mode",
        description="Choose the selection range inputs",
        items=[
            ('INCLUSIVE', "Inclusive", "Input start index and inclusive stop index"),
            ('EXCLUSIVE', "Exclusive", "Input start index and exclusive stop index"),
            ('COUNT',     "Count",     "Input start index and selection count"),
        ],
    )
    count: bpy.props.IntProperty(
        name="Count",
        description="The count of items for the selection range",
        default=1,
        min=1,
    )
    private_start: bpy.props.IntProperty(default=0, min=0)

    def update_start(self, context):
        if self.input_mode != 'COUNT':
            self.count = max(self.count + self.private_start - self.start, 1)
        self.private_start = self.start

    start: bpy.props.IntProperty(
        name="Start",
        description="The starting index for the selection range",
        default=0,
        min=0,
        update=update_start,
    )

    def get_inc_stop(self):
        return self.start + self.count - 1

    def get_exc_stop(self):
        return self.start + self.count

    def set_inc_stop(self, value):
        value = max(value, 0)
        if self.input_mode != 'COUNT' and value < self.start:
            self.start = value
            self.count = 1
        else:
            self.count = 1 + value - self.start

    def set_exc_stop(self, value):
        value = max(value, 1)
        if self.input_mode != 'COUNT' and value <= self.start:
            self.start = value - 1
            self.count = 1
        else:
            self.count = value - self.start

    inc_stop: bpy.props.IntProperty(
        name="Stop",
        description="The inclusive ending index for the selection range",
        default=0,
        min=0,
        get=get_inc_stop,
        set=set_inc_stop,
    )
    exc_stop: bpy.props.IntProperty(
        name="Stop",
        description="The exclusive ending index for the selection range",
        default=1,
        min=1,
        get=get_exc_stop,
        set=set_exc_stop,
    )
    replace_selection: bpy.props.BoolProperty(
        name="Replace Selection",
        description="Replace instead of adding to the previous selection",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        obj = context.object
        if obj and obj.type == 'MESH' and obj.mode == 'EDIT':
            return True
        return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "select_mode")
        layout.prop(self, "input_mode")
        layout.prop(self, "start")

        if self.input_mode == 'INCLUSIVE':
            layout.prop(self, "inc_stop")
        elif self.input_mode == 'EXCLUSIVE':
            layout.prop(self, "exc_stop")
        elif self.input_mode == 'COUNT':
            layout.prop(self, "count")

        layout.prop(self, "replace_selection")

    def check(self, context):
        obj = context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        if self.select_mode == 'VERTEX':
            max_len = len(bm.verts)
        elif self.select_mode == 'EDGE':
            max_len = len(bm.edges)
        else:
            max_len = len(bm.faces)
        bm.free()

        if max_len < 1:
            return False

        max_index = max_len - 1
        # Adjust start & stop if out of bounds
        if self.start > max_index:
            self.start = max_index
        stop = self.inc_stop if self.input_mode == 'INCLUSIVE' else self.exc_stop
        if stop > max_len:
            # For exclusive, stop can be equal to max_len; for inclusive it should be <= max_index
            if self.input_mode == 'EXCLUSIVE':
                stop = max_len
            else:
                stop = max_index
            # Push back into properties
            if self.input_mode == 'INCLUSIVE':
                self.inc_stop = stop
            else:
                self.exc_stop = stop
        return True

    def execute(self, context):
        if self.replace_selection:
            bpy.ops.mesh.select_all(action='DESELECT')

        obj = context.object
        me = obj.data
        bm = bmesh.from_edit_mesh(me)

        # Ensure proper mode
        if self.select_mode == 'VERTEX':
            bpy.ops.mesh.select_mode(type='VERT')
            seq = bm.verts
        elif self.select_mode == 'EDGE':
            bpy.ops.mesh.select_mode(type='EDGE')
            seq = bm.edges
        else:
            bpy.ops.mesh.select_mode(type='FACE')
            seq = bm.faces

        # Use islice to pick the items in range
        start = self.start
        stop = self.exc_stop  # exc_stop yields start+count naturally
        for item in islice(seq, start, stop):
            item.select = True

        bm.select_flush_mode()
        bmesh.update_edit_mesh(me, loop_triangles=False, destructive=False)
        return {'FINISHED'}

    def invoke(self, context, event):
        # Determine default select mode based on current mesh select mode
        sm = context.tool_settings.mesh_select_mode
        if sm[0]:
            self.select_mode = 'VERTEX'
        elif sm[1]:
            self.select_mode = 'EDGE'
        elif sm[2]:
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

if __name__ == "__main__":
    register()
