# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

from msts.TokenId import TokenId
from msts.StructuredBlockReader import BinaryBlockReader
from msts.StructuredBlockReader import StructuredBlockReader
import math
from typing import Self
from typing import List
import copy as cp

# http://www.digital-rails.com/files/MSTS%20shape%20file%20format.txt

class ShapeHeader():
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.shape_header)
        self.flags1 = block.read_flags()
        self.flags2 = None
        if (not block.end_of_block()):
            self.flags2 = block.read_flags()
        block.verify_end_of_block()

class VolSphere():
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.vol_sphere)
        vector_block = block.read_sub_block()
        self.vector = Vector()
        self.vector.x = vector_block.read_float()
        self.vector.y = vector_block.read_float()
        self.vector.z = vector_block.read_float()
        vector_block.verify_end_of_block()
        self.radius = block.read_float()
        block.verify_end_of_block()

class Volumes(List[VolSphere]):
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.volumes) 
        count = self.capacity = block.read_int()
        while count > 0:
            self.append(VolSphere(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class Vector:
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z

    def matches(self, point: Self) -> bool:
        if math.fabs(point.x - self.x) > 0.0001:
            return False
        if math.fabs(point.y - self.y) > 0.0001:
            return False
        if math.fabs(point.z - self.z) > 0.0001:
            return False
        return True

class ShaderNames(List[str]):
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.shader_names)
        count = self.capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.named_shader)
            self.append(sub_block.read_string())
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()

class TextureFilterNames(List[str]):
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.texture_filter_names)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.named_filter_mode)
            self.append(sub_block.read_string())
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()

class Point:
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def matches(self, point: Self):
        if math.fabs(point.x - self.x) > 0.0001:
            return False
        if math.fabs(point.y - self.y) > 0.0001:
            return False
        if math.fabs(point.z - self.z) > 0.0001:
            return False
        return True

class Points(List[Point]):
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.points)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.point)
            self.append(Point(sub_block.read_float(), sub_block.read_float(), sub_block.read_float()))
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()

class UvPoint():
    def __init__(self, u: float, v: float):
        self.u = u
        self.v = v

    def matches(self, point: Self) -> bool:
        if math.fabs(point.u - self.u) > 0.0001:
            return False
        if math.fabs(point.v - self.v) > 0.0001:
            return False
        return True

class UvPoints(List[UvPoint]):
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.uv_points)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.uv_point)
            self.append(UvPoint(sub_block.read_float(), sub_block.read_float()))
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()
        
class Normals(List[Vector]):
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.normals)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.vector)
            self.append(Vector(sub_block.read_float(), sub_block.read_float(), sub_block.read_float()))
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()

class SortVectors(List[Vector]):
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.sort_vectors)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.vector)
            self.append(Vector(sub_block.read_float(), sub_block.read_float(), sub_block.read_float()))
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()

class Color:
    def __init__(self, r: float, g: float, b: float, a: float):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

class Colors(List[Color]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.colours)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.colour)
            self.append(Color(a = sub_block.read_float(), r = sub_block.read_float(), g = sub_block.read_float(), b = sub_block.read_float()))
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()

class Matrix:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.matrix)
        if block.label != None:
            self.name = block.label

        self.ax = block.read_float()
        self.ay = block.read_float()
        self.az = block.read_float()

        self.bx = block.read_float()
        self.by = block.read_float()
        self.bz = block.read_float()

        self.cx = block.read_float()
        self.cy = block.read_float()
        self.cz = block.read_float()

        self.dx = block.read_float()
        self.dy = block.read_float()
        self.dz = block.read_float()

        block.verify_end_of_block()

    # def __init__(self):
    #     self.ax = 1.0
    #     self.ay = 0.0
    #     self.az = 0.0

    #     self.bx = 0.0
    #     self.by = 1.0
    #     self.bz = 0.0

    #     self.cx = 0.0
    #     self.cy = 0.0
    #     self.cz = 1.0

    #     self.dx = 0.0
    #     self.dy = 0.0
    #     self.dz = 0.0

    # def __init__(self, name: str):
    #     self.name = name

    #     self.ax = 1.0
    #     self.ay = 0.0
    #     self.az = 0.0

    #     self.bx = 0.0
    #     self.by = 1.0
    #     self.bz = 0.0

    #     self.cx = 0.0
    #     self.cy = 0.0
    #     self.cz = 1.0

    #     self.dx = 0.0
    #     self.dy = 0.0
    #     self.dz = 0.0
 
    def get(self, i: int, j: int) -> float:
        index = i * 4 + j
        if index == 0:   return self.ax
        elif index == 1: return self.ay
        elif index == 2: return self.az
        elif index == 3: return 0.0

        elif index == 4: return self.bx
        elif index == 5: return self.by
        elif index == 6: return self.bz
        elif index == 7: return 0.0

        elif index == 8:  return self.cx
        elif index == 9:  return self.cy
        elif index == 10: return self.cz
        elif index == 11: return 0.0

        elif index == 12: return self.dx
        elif index == 13: return self.dy
        elif index == 14: return self.dz
        elif index == 15: return 1.0

        else: raise Exception("Array index out of bounds")

    def set(self, i: int, j: int, value: float):
        index = i * 4 + j
        if index == 0:   self.ax = value
        elif index == 1: self.ay = value
        elif index == 2: self.az = value
        elif index == 3: pass

        elif index == 4: self.bx = value
        elif index == 5: self.by = value
        elif index == 6: self.bz = value
        elif index == 7: pass

        elif index == 8:  self.cx = value
        elif index == 9:  self.cy = value
        elif index == 10: self.cz = value
        elif index == 11: pass

        elif index == 12: self.dx = value
        elif index == 13: self.dy = value
        elif index == 14: self.dz = value
        elif index == 15: pass

        else: raise Exception("Array index out of bounds")

    def matches(self, target: Self) -> bool:
        return self.ax == target.ax and self.ay == target.ay and self.az == target.az and self.bx == target.bx and self.by == target.by and self.bz == target.bz and self.cx == target.cx and self.cy == target.cy and self.cz == target.cz and self.dx == target.dx and self.dy == target.dy and self.dz == target.dz

class Matrices(List[Matrix]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.matrices)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(Matrix(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class Images(List[str]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.images)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.image)
            self.append(sub_block.read_string())
            sub_block.verify_end_of_block()
            count -= 1
        block.verify_end_of_block()
     
class Texture:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.texture)
        self.i_image = block.read_int()
        self.filter_mode = block.read_int()
        self.mip_map_lod_bias = block.read_float()
        if not block.end_of_block():
            self.border_color = block.read_flags()
        block.verify_end_of_block()

class Textures(List[Texture]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.textures)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(Texture(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()


    # def __init__(self, new_i_image: int):
    #     self.i_image = new_i_image
    #     self.filter_mode = 0
    #     self.mip_map_lod_bias = -3
    #     self.border_color = 0xff000000
        
    def matches(self, texture: Self) -> bool:
        if not self.i_image == texture.i_image: return False
        if not self.filter_mode == texture.filter_mode: return False
        if not self.mip_map_lod_bias == texture.mip_map_lod_bias: return False
        if not self.border_color == texture.border_color: return False
        return True

class LightMaterial:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.light_material)
        self.flags = block.read_flags()
        self.DiffColIdx = block.read_int()
        self.AmbColIdx = block.read_int()
        self.SpecColIdx = block.read_int()
        self.EmissiveColIdx = block.read_int()
        self.SpecPower = block.read_float()
        block.verify_end_of_block()

class LightMaterials(List[LightMaterial]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.light_materials)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(LightMaterial(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class LightModelCfg:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.light_model_cfg)
        self.flags = block.read_flags()
        self.uv_ops = UvOps(block.read_sub_block())
        block.verify_end_of_block()

class LightModelCfgs(List[LightModelCfg]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.light_model_cfgs)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(LightModelCfg(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class UvOp:
    def __init__(self):
        self.tex_addr_mode = 0

class UvOpCopy(UvOp):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.uv_op_copy)
        self.tex_addr_mode = block.read_int()
        self.src_uv_idx = block.read_int()
        block.verify_end_of_block()

class UvOpReflectMapFull(UvOp):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.uv_op_reflectmapfull)
        self.tex_addr_mode = block.read_int()
        block.verify_end_of_block()

class UvOpReflectMap(UvOp):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.uv_op_reflectmap)
        self.tex_addr_mode = block.read_int()
        block.verify_end_of_block()

class UvOpUniformScale(UvOp):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.uv_op_uniformscale)
        self.tex_addr_mode = block.read_int()
        self.src_uv_idx = block.read_int()
        self.unknown_parameter_3 = block.read_float()
        block.verify_end_of_block()
        block.trace_information(f"{block.Id} was treated as uv_op_copy")

class UvOpNonUniformScale(UvOp):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.uv_op_nonuniformscale)
        self.tex_addr_mode = block.read_int()
        self.src_uv_idx = block.read_int()
        self.unknown_parameter_3 = block.read_float()
        self.unknown_parameter_4 = block.read_float()
        block.verify_end_of_block()
        block.trace_information(f"{block.Id} was treated as uv_op_copy")

class UvOps(List[UvOp]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.uv_ops)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            if sub_block.id == TokenId.uv_op_copy: self.append(UvOpCopy(sub_block))
            elif sub_block.id == TokenId.uv_op_reflectmapfull: self.append(UvOpReflectMapFull(sub_block))
            elif sub_block.id == TokenId.uv_op_reflectmap: self.append(UvOpReflectMap(sub_block))
            elif sub_block.id == TokenId.uv_op_uniformscale: self.append(UvOpUniformScale(sub_block))
            elif sub_block.id == TokenId.uv_op_nonuniformscale: self.append(UvOpNonUniformScale(sub_block))
            else: raise Exception(f"Unexpected uv_op: {str(sub_block.id)}")
            count -= 1
        block.verify_end_of_block()

class VtxState:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.vtx_state)
        self.flags = block.read_flags()
        self.i_matrix = block.read_int()
        self.light_mat_idx = block.read_int()
        self.light_cfg_idx = block.read_int()
        self.light_flags = block.read_flags()
        if not block.end_of_block():
            self.matrix2 = block.read_int()
        block.verify_end_of_block()

    # def __init__(self, new_imatrix: int):
    #     self.flags = 0
    #     self.i_matrix = new_imatrix
    #     self.light_mat_idx = -5
    #     self.light_cfg_idx = 0
    #     self.light_flags = 2
    #     self.matrix2 = -1

    # def __init__(self, copy: Self):
    #     self.flags = copy.flags
    #     self.i_matrix = copy.i_matrix
    #     self.light_mat_idx = copy.light_mat_idx
    #     self.light_cfg_idx = copy.light_cfg_idx
    #     self.light_flags = copy.light_flags
    #     self.matrix2 = -1

    def get_lighting(self) -> int:
        return self.light_mat_idx

    def matches(self, target: Self) -> bool:
        return self.flags == target.flags and self.i_matrix == target.i_matrix and self.light_mat_idx == target.light_mat_idx and self.light_cfg_idx == target.light_cfg_idx and self.light_flags == target.light_flags

class VtxStates(List[VtxState]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.vtx_states)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(VtxState(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class PrimState:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.prim_state)
        self.name = block.label
        self.flags = block.read_flags()
        self.i_shader = block.read_int()

        sub_block = block.read_sub_block()
        sub_block.verify_id(TokenId.tex_idxs)
        self.tex_idxs = list[int]()
        count = sub_block.read_int()
        while count > 0:
            self.tex_idxs.append(sub_block.read_int())
            count -= 1
        sub_block.verify_end_of_block()

        self.z_bias = block.read_float()
        self.i_vtx_state = block.read_int()
        self.alpha_test_mode = block.read_int()
        self.light_cfg_idx = block.read_int()
        self.z_buf_mode = block.read_int()
        block.verify_end_of_block()

    # def __init__(self, new_itexture: int, new_i_shader: int, new_i_vtx_state: int):
    #     self.flags = 0
    #     self.i_shader = new_i_shader
    #     self.tex_idxs = list[int]()
    #     self.tex_idxs.append(new_itexture)
    #     self.z_bias = 0
    #     self.i_vtx_state = new_i_vtx_state
    #     self.alpha_test_mode = 0
    #     self.light_cfg_idx = 0
    #     self.z_buf_mode = 1

    # def __init__(self, copy: Self):
    #     self.flags = copy.flags
    #     self.i_shader = copy.i_shader
    #     self.tex_idxs = cp.deepcopy(copy.tex_idxs)
    #     self.z_bias = copy.z_bias
    #     self.i_vtx_state = copy.i_vtx_state
    #     self.alpha_test_mode = copy.alpha_test_mode
    #     self.light_cfg_idx = copy.light_cfg_idx
    #     self.z_buf_mode = copy.z_buf_mode

    def get_i_texture(self) -> int:
        return self.tex_idxs[0]

    def matches(self, target: Self) -> bool:
        if not self.flags == target.flags: return False
        if not self.i_shader == target.i_shader: return False
        if not len(self.tex_idxs) == len(target.tex_idxs): return False
        if not self.tex_idxs == target.tex_idxs: return False
        if not self.z_bias == target.z_bias: return False
        if not self.i_vtx_state == target.i_vtx_state: return False
        if not self.alpha_test_mode == target.alpha_test_mode: return False
        if not self.light_cfg_idx == target.light_cfg_idx: return False
        if not self.z_buf_mode == target.z_buf_mode: return False
        return True

class PrimStates(List[PrimState]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.prim_states)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(PrimState(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class LodControl:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.lod_control)
        self.distance_levels_header = DistanceLevelsHeader(block.read_sub_block())
        self.distance_levels = DistanceLevels(block.read_sub_block())
        block.verify_end_of_block()

class LodControls(List[LodControl]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.lod_controls)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(LodControl(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class DistanceLevelsHeader:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.distance_levels_header)
        self.d_lev_bias = block.read_int()
        block.verify_end_of_block()

class DistanceLevel:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.distance_level)
        self.distance_level_header = DistanceLevelHeader(block.read_sub_block())
        self.sub_objects = SubObjects(block.read_sub_block())
        block.verify_end_of_block()

class DistanceLevels(List[DistanceLevel]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.distance_levels)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(DistanceLevel(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class DistanceLevelHeader:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.distance_level_header)

        sub_block = block.read_sub_block()
        sub_block.verify_id(TokenId.dlevel_selection)
        self.dlevel_selection = sub_block.read_float()
        sub_block.verify_end_of_block()

        sub_block = block.read_sub_block()
        sub_block.verify_id(TokenId.hierarchy)
        self.hierarchy = list[int]()
        count = sub_block.read_int()
        while count > 0:
            self.hierarchy.append(sub_block.read_int())
            count -= 1
        sub_block.verify_end_of_block()

        block.verify_end_of_block()

class SubObject:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.sub_object)
        self.sub_object_header = SubObjectHeader(block.read_sub_block())
        self.vertices = Vertices(block.read_sub_block())
        self.vertex_sets = VertexSets(block.read_sub_block())
        self.primitives = Primitives(block.read_sub_block())
        block.verify_end_of_block()

class SubObjects(List[SubObject]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.sub_objects)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(SubObject(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class SubObjectHeader:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.sub_object_header)

        self.flags = block.read_flags()
        self.sort_vector_idx = block.read_int()
        self.vol_idx = block.read_int()
        self.src_vtx_fmt_flags = block.read_flags()
        self.dst_vtx_fmt_flags = block.read_flags()
        self.geometry_info = GeometryInfo(block.read_sub_block())

        if not block.end_of_block():
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.subobject_shaders)
            self.subobject_shaders = list[int]()
            count = sub_block.read_int()
            while count > 0:
                self.subobject_shaders.append(sub_block.read_int())
                count -= 1
            sub_block.verify_end_of_block()

        if not block.end_of_block():
            sub_block = block.read_sub_block()
            sub_block.verify_id(TokenId.subobject_light_cfgs)
            self.subobject_light_cfgs = list[int]()
            count = sub_block.read_int()
            while count > 0:
                self.subobject_light_cfgs.append(sub_block.read_int())
                count -= 1
            sub_block.verify_end_of_block()

        if not block.end_of_block():
            self.sub_obj_id = block.read_int()

        block.verify_end_of_block()

class GeometryInfo:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.geometry_info)
        self.face_normals = block.read_int()
        self.tx_light_cmds = block.read_int()
        self.node_x_trilist_idxs = block.read_int() # See ORTS ShapeFile.cs is maybe not correct, it could be NodeXTxLightCmds instead of NodeXTrilistIdxs
        self.trilist_idxs = block.read_int()
        self.line_list_idxs = block.read_int()
        self.node_x_trilist_idxs = block.read_int()
        self.tri_lists = block.read_int()
        self.line_lists = block.read_int()
        self.pt_lists = block.read_int()
        self.node_x_trilists = block.read_int()
        self.geometry_nodes = GeometryNodes(block.read_sub_block())

        sub_block = block.read_sub_block()
        sub_block.verify_id(TokenId.geometry_node_map)
        self.geometry_node_map = list[int]()
        count = sub_block.read_int()
        while count > 0:
            self.geometry_node_map.append(sub_block.read_int())
            count -= 1
        sub_block.verify_end_of_block()

        block.verify_end_of_block()

class GeometryNode:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.geometry_node)
        self.tx_light_cmds = block.read_int()
        self.node_x_tx_light_cmds = block.read_int()
        self.tri_lists = block.read_int()
        self.line_lists = block.read_int()
        self.pt_lists = block.read_int()
        self.cullable_prims = CullablePrims(block.read_sub_block())
        block.verify_end_of_block()
    
    # def __init__(self):
    #     self.tx_light_cmds = 1
    #     self.node_x_tx_light_cmds = 0
    #     self.tri_lists = 0
    #     self.line_lists = 0
    #     self.pt_lists = 0
    #     self.cullable_prims = CullablePrims()

class GeometryNodes(List[GeometryNode]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.geometry_nodes)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(GeometryNode(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class CullablePrims:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.cullable_prims)
        self.num_prims = block.read_int()
        self.num_flat_sections = block.read_int()
        self.num_prim_idxs = block.read_int()
        block.verify_end_of_block()
        
    # def __init__(self):
    #     self.num_prims = 0
    #     self.num_flat_sections = 0
    #     self.num_prim_idxs = 0

class Vertex:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.vertex)
        self.flags = block.read_flags()
        self.i_point = block.read_int()
        self.i_normal = block.read_int()
        self.color1 = block.read_flags()
        self.color2 = block.read_flags()

        sub_block = block.read_sub_block()
        sub_block.verify_id(TokenId.vertex_uvs)
        self.vertex_uvs = list[int]()
        count = sub_block.read_int()
        while count > 0:
            self.vertex_uvs.append(sub_block.read_int())
            count -= 1
        sub_block.verify_end_of_block()

        block.verify_end_of_block()

    # def __init__(self, copy: Self):
    #         self.flags = copy.flags
    #         self.i_point = copy.i_point
    #         self.i_normal = copy.i_normal
    #         self.color1 = copy.color1
    #         self.color2 = copy.color2
    #         self.vertex_uvs = cp.deepcopy(copy.vertex_uvs)

    # def __init__(self):
    #     self.flags = 0
    #     self.i_point = 0
    #     self.i_normal = 0
    #     self.color1 = 0xffffffff #U
    #     self.color2 = 0xff000000 #U
    #     self.vertex_uvs = list[int]()
    #     self.vertex_uvs[0] = 0

    def matches_content(self, target: Self) -> bool:
        if not self.flags == target.flags: return False
        if not self.i_point == target.i_point: return False
        if not self.i_normal == target.i_normal: return False
        if not self.color1 == target.color1: return False
        if not self.color2 == target.color2: return False
        if not self.vertex_uvs == target.vertex_uvs: return False
        return True

class Vertices(List[Vertex]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.vertices)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(Vertex(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class VertexSet:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.vertex_set)
        self.vtx_state_idx = block.read_int()
        self.start_vtx_idx = block.read_int()
        self.vtx_count = block.read_int()
        block.verify_end_of_block()

    # def __init__(self):
    #     self.vtx_state_idx = 0
    #     self.start_vtx_idx = 0
    #     self.vtx_count = 0

class VertexSets(List[VertexSet]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.vertex_sets)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(VertexSet(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class Primitive:
    def __init__(self,  block: BinaryBlockReader, last_prim_state_idx: int):
        self.prim_state_idx = last_prim_state_idx
        self.indexed_trilist = IndexedTrilist(block)

class Primitives(List[Primitive]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.primitives)
        last_prim_state_idx = 0
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            if sub_block.id == TokenId.prim_state_idx:
                last_prim_state_idx = sub_block.read_int()
                sub_block.verify_end_of_block()
            elif sub_block.id == TokenId.indexed_trilist:
                self.append(Primitive(sub_block, last_prim_state_idx))
            else:
                raise Exception(f"Unexpected primitive type {sub_block.id}")
            count -= 1
        block.verify_end_of_block()

class IndexedTrilist:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.indexed_trilist)
        self.vertex_idxs = VertexIdxs(block.read_sub_block())

        sub_block = block.read_sub_block()
        sub_block.verify_id(TokenId.normal_idxs)
        self.normal_idxs = list[int]()
        count = sub_block.read_int()
        while count > 0:
            self.normal_idxs.append(sub_block.read_int())
            sub_block.read_int(); # skip the '3' value - its purpose unknown
            count -= 1
        sub_block.verify_end_of_block()

        sub_block = block.read_sub_block()
        sub_block.verify_id(TokenId.flags)
        self.flags = list[int]()
        count = sub_block.read_int()
        while count > 0:
            self.flags.append(sub_block.read_flags())
            count -= 1
        sub_block.verify_end_of_block()

        block.verify_end_of_block()

class VertexIdx:
    def __init__(self,  block: BinaryBlockReader):
        self.a = block.read_int()
        self.b = block.read_int()
        self.c = block.read_int()

    # def __init__(self, ia: int, ib: int, ic: int):
    #     self.a = ia
    #     self.b = ib
    #     self.c = ic
        
class VertexIdxs(List[VertexIdx]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.vertex_idxs)
        count = self.Capacity = block.read_int() // 3
        while count > 0:
            self.append(VertexIdx(block))
            count -= 1
        block.verify_end_of_block()

class Animation:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.animation)
        self.frame_count = block.read_int()
        self.frame_rate = block.read_int()
        self.anim_nodes = AnimNodes(block.read_sub_block())
        block.verify_end_of_block()

class Animations(List[Animation]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.animations)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(Animation(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class AnimNode:
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.anim_node)
        self.name = block.label
        self.controllers = Controllers(block.read_sub_block())
        block.verify_end_of_block()

class AnimNodes(List[AnimNode]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.anim_nodes)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(AnimNode(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class Controller(list):
    pass

class Controllers(List[Controller]):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.controllers)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            if sub_block.id == TokenId.linear_pos: self.append(LinearPos(sub_block))
            elif sub_block.id == TokenId.tcb_rot: self.append(TcbRot(sub_block))
            else: raise Exception(f"Unexpected animation controller {sub_block.Id}")
            count -= 1
        block.verify_end_of_block()

class KeyPosition:
    def __init__(self):
        self.frame = 0

class TcbRot(Controller):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.tcb_rot)
        count = self.Capacity = block.read_int()
        while count > 0:
            sub_block = block.read_sub_block()
            if sub_block.id == TokenId.slerp_rot: self.append(SlerpRot(sub_block))
            elif sub_block.id ==  TokenId.tcb_key: self.append(TcbKey(sub_block))
            else: raise Exception(f"Unexpected block {sub_block.id}")
            count -= 1
        block.verify_end_of_block()

class SlerpRot(KeyPosition):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.slerp_rot)
        self.frame = block.read_int()
        self.x = block.read_float()
        self.y = block.read_float()
        self.z = block.read_float()
        self.w = block.read_float()
        block.verify_end_of_block()

class LinearPos(Controller):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.linear_pos)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(LinearKey(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class LinearKey(KeyPosition):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.linear_key)
        self.frame = block.read_int()
        self.x = block.read_float()
        self.y = block.read_float()
        self.z = block.read_float()
        block.verify_end_of_block()

class TcbPos(Controller):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.tcb_pos)
        count = self.Capacity = block.read_int()
        while count > 0:
            self.append(TcbKey(block.read_sub_block()))
            count -= 1
        block.verify_end_of_block()

class TcbKey(KeyPosition):
    def __init__(self,  block: BinaryBlockReader):
        block.verify_id(TokenId.tcb_key)
        self.frame = block.read_int()
        self.x = block.read_float()
        self.y = block.read_float()
        self.z = block.read_float()
        self.w = block.read_float()
        self.tension = block.read_float()
        self.continuity = block.read_float()
        self.bias = block.read_float()
        self.in_ = block.read_float()
        self.out = block.read_float()
        block.verify_end_of_block()

class Shape():
    def __init__(self, block: BinaryBlockReader):
        block.verify_id(TokenId.shape)
        self.shape_header = ShapeHeader(block.read_sub_block())
        self.volumes = Volumes(block.read_sub_block())
        self.shader_names = ShaderNames(block.read_sub_block())
        self.texture_filter_names = TextureFilterNames(block.read_sub_block())
        self.points = Points(block.read_sub_block())
        self.uv_points = UvPoints(block.read_sub_block())
        self.normals = Normals(block.read_sub_block())
        self.sort_vectors = SortVectors(block.read_sub_block())
        self.colors = Colors(block.read_sub_block())
        self.matrices = Matrices(block.read_sub_block())
        self.images = Images(block.read_sub_block())
        self.textures = Textures(block.read_sub_block())
        self.light_materials = LightMaterials(block.read_sub_block())
        self.light_model_cfgs = LightModelCfgs(block.read_sub_block())
        self.vtx_states = VtxStates(block.read_sub_block())
        self.prim_states = PrimStates(block.read_sub_block())
        self.lod_controls = LodControls(block.read_sub_block())
        if not block.end_of_block():
            self.animations = Animations(block.read_sub_block())
        block.verify_end_of_block()

    @staticmethod
    def FromFile(filename: str) -> Self:
        file = StructuredBlockReader.Open(filename)
        shape = Shape(file.read_sub_block())
        return shape