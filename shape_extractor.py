# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

from msts.ShapeFile import *

import os
import json

from pliskin.BinaryWriter import BinaryWriter
from pliskin.BinaryReader import BinaryReader
import pliskin.gltf
from pliskin.gltf import GltfHelper
from pliskin.logger import Logger
from pliskin.Vec3f import Vec3f, Mat3x3f, Transformation, Quaternion
from texture_extractor import TextureExtractor

from io import BytesIO

class ShapeExtractor:

    def __init__(self, shape_file: str, output_dir : str, format : str = "orts", reflect_z : bool = True):
        self._shape_file = shape_file
        self._output_dir = output_dir
        self._format = format
        self._reflect_z = reflect_z
        self._current_dir = os.path.dirname(shape_file)
        self._shape_name = os.path.basename(shape_file)[:-2]
        
        self._anims_3dts = list()

        self._gltf_lods = list()
        self._buffer_lods = list()
        self._buffer_name_lods = list() # TODO, reuse name in gltf instead
        self._lod_poly_count = list() # TODO, refactor name

        self._use_dds = self._isOrts()
        self._use_lod = self._isOrts()

        self._M_TRANSF:Mat3x3f = Mat3x3f.diag(1,1,-1) if self._reflect_z else Mat3x3f.identity()
        self._V_TRANSF:Vec3f = Vec3f(1,1,-1) if self._reflect_z else Vec3f(1,1,1)
        self._Q_TRANSF:Quaternion = Quaternion(1,1,-1,-1) if self._reflect_z else Quaternion(1,1,1,1)
        self._Q_TCBK:Quaternion = Quaternion(1,1,-1,1) if self._reflect_z else Quaternion(1,1,1,1)

    def run(self) -> None:
        self._load_shape()
        if not os.path.exists(self._output_dir): os.makedirs(self._output_dir)
        self._extract_textures()
        self._extract_lods()

    def _is3dts(self) -> bool:
        return self._format == "3dts"
    
    def _isOrts(self) -> bool:
        return self._format == "orts"

    def _load_shape(self) -> None:
        # LOAD SHAPE
        Logger.log(f"LOAD SHAPE \"{self._shape_file}\"")
        self._shape : Shape = Shape.FromFile(self._shape_file)

    def _extract_textures(self) -> None:
        # EXTRACT IMAGES & TEXTURES
        Logger.log("EXTRACT IMAGES & TEXTURES")
        assert os.path.exists(self._output_dir), f"Path {self._output_dir} does not exist."
        ace_extractor = TextureExtractor(self._output_dir)
        for image in self._shape.images:
            texture_filename = os.path.join(self._current_dir, image)
            
            ace_extractor.save_png(texture_filename)
            if (self._use_dds):
                ace_extractor.save_dds(texture_filename) 
            

    def print_stats(self) -> None:
        gltf = self._gltf_helper.get_dict()
        print(f"GLTF:{self._gltf_helper._file_name}")
        
        print(f"buffer size:{gltf['buffers'][0]['byteLength']}")
        print(f"vertex count:{self._gltf_helper._vertex_count}")
        print(f"triangle count:{self._gltf_helper._triangle_count}")

        print(f"scenes:{len(gltf['scenes'])}")
        print(f"nodes:{len(gltf['nodes'])}")
        print(f"buffers:{len(gltf['buffers'])}")
        print(f"bufferViews:{len(gltf['bufferViews'])}")
        print(f"accessors:{len(gltf['accessors'])}")
        print(f"images:{len(gltf['images'])}")
        print(f"textures:{len(gltf['textures'])}")
        print(f"materials:{len(gltf['materials'])}")
        print(f"samplers:{len(gltf['samplers'])}")

        print(f"meshes:{len(gltf['meshes'])}")
        i = 0
        for mesh in gltf['meshes']:
            i += len(mesh['primitives'])
        print(f"meshes.primitives:{i}")

        print(f"animations:{len(gltf['animations'])}")
        j = k = 0
        for animation in gltf['animations']:
            j += len(animation['channels'])
            k += len(animation['samplers'])
        print(f"animations.channels:{j}")
        print(f"animations.samplers:{k}")

    def _get_alphaMode(shader:str) -> str:
        if shader == 'TexDiff':
            return "OPAQUE"
        elif shader == 'BlendATexDiff':
            return "BLEND" # MASK ?
        
        raise Exception(f"Shader {shader} not implemented.")

    def _save_gltf(self) -> None:
        with open(self._gltf_helper._file_name, 'w', encoding='utf-8') as f:
            json.dump(self._gltf_helper.get_dict(), f, ensure_ascii=False, indent=4) 

    def _copy_buffer(self, i_source:int, source:BinaryWriter, i_destination:int, destination:BinaryWriter) -> None:
        byteOffset = destination.get_size()
        destination.write_bytes(source.get_bytes())
        byteLength = source.get_size()
        self._gltf_helper.get_bufferView(i_source)["byteLength"] = byteLength
        self._gltf_helper.get_bufferView(i_source)["byteOffset"] = byteOffset
        self._gltf_helper.get_buffer(i_destination)['byteLength'] = destination.get_size()

    def _rename_nodes(self, names:dict) -> None:
        for node in self._gltf_helper.get_dict()['nodes']:
            if node['name'] in names:
                Logger.log(f"RENAME NODE {node['name']} to {names[node['name']]}")
                node['name'] = names[node['name']]

    def _rekey_animation(self, bw:BinaryWriter) -> None:
        FRAME_RATE = 24
        br = BinaryReader(BytesIO(bw.get_bytes()))
        _seek = bw.seek(0 ,1)
        
        rekey_offset = 0.0
        for animation in self._gltf_helper.get_dict()['animations']:
            if len(animation['samplers']) == 0: continue

            Logger.log(f"REKEY ANIMATION {animation['name']}")

            # _max = self._gltf_helper.get_accessor(animation['samplers'][0]['input'])['max']
            # _min = self._gltf_helper.get_accessor(animation['samplers'][0]['input'])['min']
            start_key = end_key = -1

            for sampler in animation['samplers']:
                i_accessor = sampler['input']
                accessor = self._gltf_helper.get_accessor(i_accessor)

                # assert accessor['max'] == _max, f"accessor.max {accessor['max']} is not {_max}."
                # assert accessor['min'] == _min, f"accessor.min {accessor['min']} is not {_min}."
                assert accessor['type'] == 'SCALAR', f"accessor.type {accessor['type']} is not SCALAR."
                assert accessor['componentType'] == pliskin.gltf.FLOAT, f"accessor.type {accessor['componentType']} is not {pliskin.gltf.FLOAT}."

                i_bufferView = accessor['bufferView']
                byteOffset = accessor['byteOffset']

                bufferView = self._gltf_helper.get_bufferView(i_bufferView)
                byteOffset += bufferView['byteOffset']

                br.seek(byteOffset)
                bw.seek(byteOffset)
                count = accessor['count']
                for i in range(0, count):
                    key = br.read_single()
                    key += rekey_offset
                    bw.write_single(key)
                    if i == 0: start_key = key
                    elif i == count-1: end_key = key
 
                accessor['min'] = [start_key]
                accessor['max'] = [end_key]
            
            anim_3dts = '; '.join([animation['name'], str(int(start_key*FRAME_RATE)), str(int(end_key*FRAME_RATE)), 'NoAutoPlay', 'Loop' if 'WIPER' in animation['name'] else 'NoLoop'])
            if not anim_3dts in self._anims_3dts:
                self._anims_3dts.append(anim_3dts)
            rekey_offset = end_key + 1.0

        bw.seek(_seek)
        for anim_3dts in self._anims_3dts:
            print(anim_3dts)

    def _save_3dts_anims(self) -> None:
        Logger.log(f"SAVE ANIMS")

        assert os.path.exists(self._output_dir), f"Path {self._output_dir} does not exist."

        anim_name = os.path.join(self._output_dir, self._shape_name + '.anim')
        with open(anim_name, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._anims_3dts))

    def _find_animation_sampler(self, i_animation:int, input:int, interpolation:str, output:int):
        for idx, sampler in enumerate(self._gltf_helper.get_dict()['animations'][i_animation]['samplers']):
            if sampler['input'] == input and sampler['interpolation'] == interpolation and sampler['output'] == output:
                return idx, sampler
        return -1, None

    def _copy_animation_by_name(self, name_source:str, name_destination:str) -> None:
        i_animation_destination, _ = self._get_animation_by_name(name_destination)
        _, animation_source = self._get_animation_by_name(name_source)
        for anim_channel in animation_source['channels']:
            i_animation_sampler = anim_channel['sampler']
            animation_sampler = animation_source['samplers'][i_animation_sampler]

            i_animation_sampler, _ = self._find_animation_sampler(i_animation_destination, animation_sampler['input'], animation_sampler['interpolation'], animation_sampler['output'])
            if i_animation_sampler == -1:
                i_animation_sampler = self._gltf_helper.create_animation_sampler(i_animation_destination, animation_sampler)
            self._gltf_helper.create_animation_channel(i_animation_destination, {"sampler": i_animation_sampler, "target": anim_channel['target']})

    def _delete_animation_by_name(self, name:str) -> None:
        i_anim, _ = self._get_animation_by_name(name)
        self._gltf_helper.get_dict()['animations'].__delitem__(i_anim)

    def _get_animation_by_name(self, name:str):
        idx, anim = self._find_animation_by_name(name)
        if idx == -1: raise Exception(f"Animation \'{name}\'not found")    
        return idx, anim
        
    def _find_animation_by_name(self, name:str):
        for idx, anim in enumerate(self._gltf_helper.get_dict()['animations']):
            if anim['name'] == name: return idx, anim
        return -1, None
    
    def _find_material(self, name:str, t_id:int, alphaMode:str):
        for idx, material in enumerate(self._gltf_helper.get_dict()['materials']):
            if material['name'] == name and material['pbrMetallicRoughness']['baseColorTexture']['index'] == t_id and material['alphaMode'] == alphaMode: return idx, material
        return -1, None
    
    def _merge_animation_by_names(self, name:str, names:list[str], delete:bool = True) -> None:
        for n in names:
            i, _ = self._find_animation_by_name(n)
            if i == -1:
                #Logger.log(f"MERGE ANIMATION {name}, {names} SKIPPED")
                return
        
        Logger.log(f"MERGE ANIMATION {name}, {names}")
        _ = self._gltf_helper.create_animation({"name": name})
        
        for n in names: 
            self._copy_animation_by_name(n, name)
            if delete:
                self._delete_animation_by_name(n)

    def _refactor_animation_for_3dts(self, bw:BinaryWriter) -> None:
        Logger.log(f"POST PROCESS 3D TRAIN STUDIO")

        Logger.log("MERGE ANIMATION")
        # TODO, case insensitive
        # TODO, PantographMiddle1A
        self._merge_animation_by_names("PANTOGRAPH1", ["PANTOGRAPHBOTTOM1", "PANTOGRAPHTOP1"])
        self._merge_animation_by_names("PANTOGRAPH2", ["PANTOGRAPHBOTTOM2", "PANTOGRAPHTOP2"])
        self._merge_animation_by_names("WIPER1", ["WIPERARMRIGHT1", "WIPERBLADERIGHT1", "WIPERARMLEFT1", "WIPERBLADELEFT1"])
        self._merge_animation_by_names("MIRROR1", ["MIRRORRIGHT1", "MIRRORLEFT1"])

        self._merge_animation_by_names("PANTOGRAPH1", ["PantographBottom1A", "PantographBottom1B", "PantographMiddle1A", "PantographMiddle1B", "PantographTop1A", "PantographTop1B"])
        self._merge_animation_by_names("PANTOGRAPH2", ["PantographBottom2A", "PantographBottom2B", "PantographMiddle2A", "PantographMiddle2B", "PantographTop2A", "PantographTop2B", "PantographMiddle2C", "PantographMiddle2D", "PantographMiddle2E", "PantographMiddle2F"])
        #self._merge_animation_by_names("MIRROR1", ["MIRRORRIGHT1", "MIRRORLEFT1"])

        Logger.log("REKEY ANIMATION")
        self._rekey_animation(bw)

        # Rename nodes from MSTS to 3D Train Studio
        Logger.log("RENAME NODE")
        #TODO, case insensitive
        rename_dict = {
            'Bogie1': '_WheelSet0',
            'BOGIE1': '_WheelSet0',
            'Wheels11': '_Wheel',
            'WHEELS11': '_Wheel',
            'Wheels12': '_Wheel',
            'WHEELS12': '_Wheel',
            'Bogie2': '_WheelSet1',
            'BOGIE2': '_WheelSet1',
            'Wheels21': '_Wheel',
            'WHEELS21': '_Wheel',
            'Wheels22': '_Wheel',
            'WHEELS22': '_Wheel'
            }
        self._rename_nodes(rename_dict)
    
    def _refactor_animation_for_orts(self, bw:BinaryWriter) -> None:
        Logger.log(f"POST PROCESS OPEN RAILS")

        Logger.log("TAG ANIMATION")
        animation_tags = ["bogie", "wheel"]
        for node in self._gltf_helper.get_dict()['nodes']:
            for tag in animation_tags:
                if node['name'].lower().startswith(tag):
                    Logger.log(f"TAG ANIMATION {node['name']}")
                    node['extras'] = { "OPENRAILS_animation_name": node['name'] }
                    break

        Logger.log("REKEY ANIMATION")
        self._rekey_animation(bw)

    def _extract_lod_textures(self) -> None: 
        png_map = dict()
        dds_map = dict()

        Logger.log(f"CONVERT TEXTURES TO PNG")
        if self._use_dds:
            Logger.log(f"CONVERT TEXTURES TO DDS")
            self._gltf_helper.add_extension("MSFT_texture_dds", required=False)

        for i, image in enumerate(self._shape.images):
            png_map[i] = self._gltf_helper.create_image({"uri": image[:-4]+".png"})
            if self._use_dds:
                dds_map[i] = self._gltf_helper.create_image({"uri": image[:-4]+".dds"})

        #TODO, create images and textures only if used by LOD

        for texture in self._shape.textures:
            assert texture.border_color == 0xff000000, f"texture.border_color {texture.border_color:x8} is not 0xff000000."
            assert texture.mip_map_lod_bias == -3 or texture.mip_map_lod_bias == 0, f"texture.mip_map_lod_bias {texture.mip_map_lod_bias} is not -3 or 0."
            assert texture.filter_mode == 0, f"texture filter_mode {texture.filter_mode} is not 0."
            
            if self._use_dds:
                self._gltf_helper.create_texture({"sampler":texture.filter_mode, "source":png_map[texture.i_image], "extensions": { "MSFT_texture_dds": { "source": dds_map[texture.i_image] }}})
            else:
                self._gltf_helper.create_texture({"sampler":texture.filter_mode, "source":png_map[texture.i_image]})
            
        for filter in self._shape.texture_filter_names:
            assert filter in ["Linear", "MipLinear"], f"filter {filter} is not Linear or MipLinear."
            self._gltf_helper.create_sampler({"magFilter": pliskin.gltf.LINEAR, "minFilter": pliskin.gltf.LINEAR, "wrapS": pliskin.gltf.REPEAT, "wrapT": pliskin.gltf.REPEAT, "name": filter})

    def _save_gltfs_and_buffers_for_3dts(self) -> None:
        # LOD recommendations with 30% poly count reduction
        print("SAVE GLTF & BUFFER, RECOMMENDED LODn with 30% poly count reduction")
        next_best_lod_poly_count = self._lod_poly_count[0]
        i_best_lod = 0
        for i_lod, poly_count in enumerate(self._lod_poly_count):
            if poly_count <= next_best_lod_poly_count and i_best_lod < 3:
                print(f"LOD{i_lod} {poly_count} → recommended as LOD{i_best_lod}")

                bw_lod:BinaryWriter = self._buffer_lods[i_lod]
                gltf_lod:GltfHelper = self._gltf_lods[i_lod]
                buffer_name = self._buffer_name_lods[i_lod].replace(f"LOD{i_lod:02}", f"LOD{i_best_lod}")
                with open(buffer_name, 'wb') as f:
                    f.write(bw_lod.get_bytes())

                assert len(gltf_lod._json['buffers']) == 1, f"len(gltf_lod._json['buffers']) {len(gltf_lod._json['buffers'])} is not 1."
                gltf_lod._json['buffers'][0]['uri'] = os.path.basename(buffer_name)
                gltf_name = gltf_lod._file_name.replace(f"LOD{i_lod:02}", f"LOD{i_best_lod}")
                with open(gltf_name, 'w', encoding='utf-8') as f:
                    json.dump(gltf_lod.get_dict(), f, ensure_ascii=False, indent=4) 

                next_best_lod_poly_count = poly_count * 0.7
                i_best_lod += 1
            else:
                print(f"LOD{i_lod} {poly_count} → IGNORED")

    def _save_gltfs_and_buffers(self) -> None:
        if self._is3dts():
            self._save_gltfs_and_buffers_for_3dts()
            return

        print("SAVE GLTF & BUFFER")
        for i_lod, poly_count in enumerate(self._lod_poly_count):
            bw_lod:BinaryWriter = self._buffer_lods[i_lod]
            gltf_lod:GltfHelper = self._gltf_lods[i_lod]
            buffer_name = self._buffer_name_lods[i_lod]
            with open(buffer_name, 'wb') as f:
                f.write(bw_lod.get_bytes())

            gltf_name = gltf_lod._file_name
            with open(gltf_name, 'w', encoding='utf-8') as f:
                json.dump(gltf_lod.get_dict(), f, ensure_ascii=False, indent=4) 

    def _cleanup_gltf(self) -> None:
        for gltf_lod in self._gltf_lods:
            gltf_dict = gltf_lod.get_dict()

            if len(gltf_dict.get('animations', [])) == 0:
                gltf_dict.pop('animations', None)

            if len(gltf_dict.get('extensionsUsed', [])) == 0:
                gltf_dict.pop('extensionsUsed', None)

            if len(gltf_dict.get('extensionsRequired', [])) == 0:
                gltf_dict.pop('extensionsRequired', None)

    def _extract_animations(self, dlevel: int, matrix2nodes: list, bw: BinaryWriter, i_buffer: int) -> None:
        Logger.log(f"EXTRACT ANIMATIONS")

        shape = self._shape
        gltf_helper = self._gltf_helper
        Q_TCBK = self._Q_TCBK
        V_TRANSF = self._V_TRANSF

        if not hasattr(shape, 'animations') or not shape.animations:
            Logger.log(f"EXTRACT ANIMATIONS skipped (no animations)")
            return
        
        # TODO create animation only if used by LOD

        key_bw = BinaryWriter(BytesIO())
        rot_bw = BinaryWriter(BytesIO())
        lin_bw = BinaryWriter(BytesIO())

        i_key_bufferView = -1     
        i_rot_bufferView = -1  
        i_lin_bufferView = -1  

        assert len(shape.animations) == 1, f"len(shape.animations) {len(shape.animations)} is not 1."
        for i, anim_node in enumerate(shape.animations[0].anim_nodes):
            assert anim_node.name == shape.matrices[i].name, f"anim_node.name {i} {anim_node.name} is not matrice.name {i} {shape.matrices[i].name}."

            if len(anim_node.controllers) == 0:
                #Logger.log(f"EXTRACT ANIMATION {anim_node.name} is empty & skipped")
                continue

            Logger.log(f"EXTRACT ANIMATION {anim_node.name}")
            i_animation =  gltf_helper.create_animation({"name": f"{anim_node.name}"})

            for controller in anim_node.controllers:           
                if isinstance(controller, TcbRot): 
                    if i_key_bufferView == -1: i_key_bufferView = gltf_helper.create_bufferView({"buffer": i_buffer, "byteLength": -1, "byteOffset": -1, "name": f"LOD{dlevel} {anim_node.name} animation buffer for sampler input"})     
                    if i_rot_bufferView == -1: i_rot_bufferView = gltf_helper.create_bufferView({"buffer": i_buffer, "byteLength": -1, "byteOffset": -1, "name": f"LOD{dlevel} {anim_node.name}.rotation animation buffer for sampler output"})  

                    i_accessor_sampler_output = gltf_helper.create_accessor({"bufferView": i_rot_bufferView, "byteOffset": rot_bw.get_size(), "componentType": pliskin.gltf.FLOAT, "count": len(controller), "type": "VEC4", "name": f"{anim_node.name}.rotation animation accessor for sampler output"})
                    i_accessor_sampler_intput = gltf_helper.create_accessor({"bufferView": i_key_bufferView, "byteOffset": key_bw.get_size(), "componentType": pliskin.gltf.FLOAT, "count": len(controller), "type": "SCALAR", "min": [-1], "max": [-1], "name": f"{anim_node.name}.rotation animation accessor for sampler input"})
                    i_animation_sampler = gltf_helper.create_animation_sampler(i_animation, {"input": i_accessor_sampler_intput, "interpolation": "LINEAR", "output": i_accessor_sampler_output})
                    for i_node in matrix2nodes[i]:
                        gltf_helper.create_animation_channel(i_animation, {"sampler": i_animation_sampler, "target": { "node": i_node, "path": "rotation"}})

                    frame_min = frame_max = controller[0].frame * 1.0# animation.frame_rate
                    for key in controller:
                        assert isinstance(key, TcbKey) , f"Key {type(key)} is not TcbKey."
                        
                        quat = Q_TCBK ** Quaternion(key.x, key.y, key.z, key.w)
                        rot_bw.write_single(quat.x)
                        rot_bw.write_single(quat.y)
                        rot_bw.write_single(quat.z)
                        rot_bw.write_single(quat.w)

                        frame = key.frame * 1.0# animation.frame_rate
                        frame_min = min(frame_min, frame)
                        frame_max = max(frame_max, frame)
                        key_bw.write_single(frame)

                    gltf_helper.get_accessor(i_accessor_sampler_intput)['min'] = [frame_min]
                    gltf_helper.get_accessor(i_accessor_sampler_intput)['max'] = [frame_max]

                elif isinstance(controller, LinearPos):
                    if i_key_bufferView == -1: i_key_bufferView = gltf_helper.create_bufferView({"buffer": i_buffer, "byteLength": -1, "byteOffset": -1, "name": f"LOD{dlevel} {anim_node.name} animation buffer for sampler input"})     
                    if i_lin_bufferView == -1: i_lin_bufferView = gltf_helper.create_bufferView({"buffer": i_buffer, "byteLength": -1, "byteOffset": -1, "name": f"LOD{dlevel} {anim_node.name}.linear animation buffer for sampler output"})  

                    i_accessor_sampler_output = gltf_helper.create_accessor({"bufferView": i_lin_bufferView, "byteOffset": lin_bw.get_size(), "componentType": pliskin.gltf.FLOAT, "count": len(controller), "type": "VEC3", "name": f"{anim_node.name}.translation animation accessor for sampler output"})
                    i_accessor_sampler_intput = gltf_helper.create_accessor({"bufferView": i_key_bufferView, "byteOffset": key_bw.get_size(), "componentType": pliskin.gltf.FLOAT, "count": len(controller), "type": "SCALAR", "min": [-1], "max": [-1], "name": f"{anim_node.name}.translation animation accessor for sampler input"})
                    
                    i_animation_sampler = gltf_helper.create_animation_sampler(i_animation, {"input": i_accessor_sampler_intput, "interpolation": "LINEAR", "output": i_accessor_sampler_output})
                    
                    for i_node in matrix2nodes[i]:
                        gltf_helper.create_animation_channel(i_animation, {"sampler": i_animation_sampler, "target": { "node": i_node, "path": "translation"}})

                    frame_min = frame_max = controller[0].frame * 1.0# animation.frame_rate
                    for key in controller:
                        assert isinstance(key, LinearKey) , f"Key {type(key)} is not LinearKey."
                        vec = V_TRANSF ** Vec3f(key.x, key.y, key.z)
                        lin_bw.write_single(vec.x)
                        lin_bw.write_single(vec.y)
                        lin_bw.write_single(vec.z)

                        frame = key.frame * 1.0# animation.frame_rate
                        frame_min = min(frame_min, frame)
                        frame_max = max(frame_max, frame)
                        key_bw.write_single(frame)

                    gltf_helper.get_accessor(i_accessor_sampler_intput)['min'] = [frame_min]
                    gltf_helper.get_accessor(i_accessor_sampler_intput)['max'] = [frame_max]

                else:
                    raise Exception(f"Controller {type(controller)} not Implemented.")  
        
        Logger.log(f"MAKE BUFFER")
        if key_bw.get_size() > 0: self._copy_buffer(i_key_bufferView, key_bw, i_buffer, bw) 
        if rot_bw.get_size() > 0: self._copy_buffer(i_rot_bufferView, rot_bw, i_buffer, bw)
        if lin_bw.get_size() > 0: self._copy_buffer(i_lin_bufferView, lin_bw, i_buffer, bw)

        if self._is3dts(): self._refactor_animation_for_3dts(bw)
        elif self._isOrts(): self._refactor_animation_for_orts(bw)

    def _extract_lods(self) -> None:
        shape = self._shape
        shape_name = self._shape_name
        V_TRANSF = self._V_TRANSF
        Q_TRANSF = self._Q_TRANSF

        # EXTRACT MESH
        Logger.log(f"EXTRACT MESH")
        assert os.path.exists(self._output_dir), f"Path {self._output_dir} does not exist."

        #for lod_control in shape.lod_controls:
        assert len(shape.lod_controls) == 1, f"len(shape.lod_controls) {len(shape.lod_controls)} is not 1."
        lod_control = shape.lod_controls[0]

        for i_lod, distance_level in enumerate(lod_control.distance_levels):
            file_suffix = f"_LOD{i_lod:02}" if i_lod > 0 else ''
            buffer_name = os.path.join(self._output_dir, shape_name + file_suffix  + '.bin')
            self._buffer_name_lods.append(buffer_name)
            gltf_name = os.path.join(self._output_dir, shape_name + file_suffix + '.gltf')

            # INIT
            matrix2nodes = list()
            for i, _ in enumerate(shape.matrices):
                matrix2nodes.append(list())

            self._gltf_helper = gltf_helper = GltfHelper(gltf_name)
            self._gltf_lods.append(self._gltf_helper)

            self._extract_lod_textures()

            dlevel = distance_level.distance_level_header.dlevel_selection
            Logger.log(f"EXTRACT MESH LOD{dlevel}")

            bw = BinaryWriter(BytesIO())
            self._buffer_lods.append(bw)
            i_buffer = gltf_helper.create_buffer({"byteLength": -1 , "uri": os.path.basename(buffer_name)})

            matrix2node = dict()

            # Pre-create nodes for all matrices, parents first (empty nodes, no mesh yet)
            hierarchy = distance_level.distance_level_header.hierarchy

            def _ensure_node(i_mat: int) -> int:
                if i_mat in matrix2node:
                    return matrix2node[i_mat]
                i_parent = hierarchy[i_mat]
                if i_parent != -1:
                    _ensure_node(i_parent)
                _matrix = shape.matrices[i_mat]
                transf = Transformation(_matrix.ax, _matrix.ay, _matrix.az, _matrix.bx, _matrix.by, _matrix.bz, _matrix.cx, _matrix.cy, _matrix.cz, _matrix.dx, _matrix.dy, _matrix.dz)
                quat: Quaternion = Q_TRANSF ** Quaternion.FromMatrix(transf.get_rotation())
                transl = V_TRANSF ** transf.get_translation()
                i_node = gltf_helper.create_node({"name": _matrix.name, "translation": [transl.x, transl.y, transl.z], "rotation": [quat.x, quat.y, quat.z, quat.w]})
                matrix2node[i_mat] = i_node
                matrix2nodes[i_mat].append(i_node)
                return i_node

            # Create nodes only for matrices used in this LOD, plus their ancestors
            for sub_object in distance_level.sub_objects:
                for primitive in sub_object.primitives:
                    prim_state = shape.prim_states[primitive.prim_state_idx]
                    vtx_state = shape.vtx_states[prim_state.i_vtx_state]
                    _ensure_node(vtx_state.i_matrix)

            for i_sub_object, sub_object in enumerate(distance_level.sub_objects):
                Logger.log(f"EXTRACT MESH LOD{dlevel}_SUBOBJECT{i_sub_object}")

                # EXTRACT VERTICES : POSITIONS, NORMALS, UVS
                i_bufferView_array = gltf_helper.create_bufferView({"buffer": i_buffer, "byteLength": -1, "byteOffset": -1, "byteStride": 12+12+8, "target": pliskin.gltf.ARRAY_BUFFER, "name": f"{shape_name}_LOD{dlevel}_SUBOBJECT{i_sub_object}_vertices"})
                start_pos = bw.get_size()

                for i, vertex in enumerate(sub_object.vertices):
                    # POSITION
                    p = shape.points[vertex.i_point]
                    p_vect = V_TRANSF ** Vec3f(p.x, p.y, p.z)
                    p_x = p_vect.x
                    p_y = p_vect.y
                    p_z = p_vect.z

                    if i==0: 
                        p_max_x = p_min_x = p_x
                        p_max_y = p_min_y = p_y
                        p_max_z = p_min_z = p_z

                    bw.write_single(p_x); p_min_x = min(p_min_x, p_x); p_max_x = max(p_max_x, p_x) 
                    bw.write_single(p_y); p_min_y = min(p_min_y, p_y); p_max_y = max(p_max_y, p_y)  
                    bw.write_single(p_z); p_min_z = min(p_min_z, p_z); p_max_z = max(p_max_z, p_z)

                    # NORMAL
                    n = shape.normals[vertex.i_normal]
                    n_vect = V_TRANSF ** Vec3f(n.x, n.y, n.z)
                    #assert abs(n_vect.magnitude() - 1.0) < 1e-6, f"NORMAL is not of unit length {n_vect} {n_vect.magnitude()}"
                    n_x = n_vect.x
                    n_y = n_vect.y
                    n_z = n_vect.z

                    if i==0: 
                        n_max_x = n_min_x = n_x
                        n_max_y = n_min_y = n_y
                        n_max_z = n_min_z = n_z

                    bw.write_single(n_x); n_min_x = min(n_min_x, n_x); n_max_x = max(n_max_x, n_x) 
                    bw.write_single(n_y); n_min_y = min(n_min_y, n_y); n_max_y = max(n_max_y, n_y)  
                    bw.write_single(n_z); n_min_z = min(n_min_z, n_z); n_max_z = max(n_max_z, n_z)

                    # UV
                    t = shape.uv_points[vertex.vertex_uvs[0]]
                    bw.write_single(t.u)
                    bw.write_single(t.v)

                    self._gltf_helper._vertex_count += 1

                p_min = [p_min_x, p_min_y, p_min_z]
                p_max = [p_max_x, p_max_y, p_max_z]
                n_min = [n_min_x, n_min_y, n_min_z]
                n_max = [n_max_x, n_max_y, n_max_z]

                end_pos = bw.get_size()
                length = end_pos - start_pos

                gltf_helper.get_buffer(i_buffer)['byteLength'] = bw.get_size()
                gltf_helper.get_bufferView(i_bufferView_array)['byteLength'] = length
                gltf_helper.get_bufferView(i_bufferView_array)['byteOffset'] = start_pos
                
                i_accessor_position = gltf_helper.create_accessor({"bufferView": i_bufferView_array, "byteOffset": 0, "componentType": pliskin.gltf.FLOAT, "count": len(sub_object.vertices), "type": "VEC3", "min": p_min, "max": p_max, "name": f"{shape_name}_LOD{dlevel}_SUBOBJECT{i_sub_object}_positions"})
                i_accessor_normal = gltf_helper.create_accessor({"bufferView": i_bufferView_array, "byteOffset": 12, "componentType": pliskin.gltf.FLOAT, "count": len(sub_object.vertices), "type": "VEC3", "min": n_min, "max": n_max, "name": f"{shape_name}_LOD{dlevel}_SUBOBJECT{i_sub_object}_normals"})
                i_accessor_texcoord_0 = gltf_helper.create_accessor({"bufferView": i_bufferView_array, "byteOffset": 12+12, "componentType": pliskin.gltf.FLOAT, "count": len(sub_object.vertices), "type": "VEC2", "name": f"{shape_name}_LOD{dlevel}_SUBOBJECT{i_sub_object}_texcoords_0"})

                # EXTRACT PRIMITIVE INDICES
                i_bufferView_element_array = gltf_helper.create_bufferView({"buffer": i_buffer, "byteLength": -1, "byteOffset": -1, "target": pliskin.gltf.ELEMENT_ARRAY_BUFFER, "name": f"{shape_name}_LOD{dlevel}_SUBOBJECT{i_sub_object}_indices"})
                start_pos = bw.get_size()
                offset = 0
                for i_primitive, primitive in enumerate(sub_object.primitives):
                    flip = True if self._reflect_z else False
                    for vertex_idx in primitive.indexed_trilist.vertex_idxs:
                        if not flip:
                            bw.write_uint16(vertex_idx.a)
                            bw.write_uint16(vertex_idx.b)
                            bw.write_uint16(vertex_idx.c)
                        else:
                            bw.write_uint16(vertex_idx.c)
                            bw.write_uint16(vertex_idx.b)
                            bw.write_uint16(vertex_idx.a)

                        self._gltf_helper._triangle_count += 1

                    i_accessor_primitive = gltf_helper.create_accessor({"bufferView": i_bufferView_element_array, "byteOffset": offset, "componentType": pliskin.gltf.UINT16, "count": len(primitive.indexed_trilist.vertex_idxs)*3, "type": "SCALAR", "name": f"{shape_name}_LOD{dlevel}_SUBOBJECT{i_sub_object}_PRIMITIVE{i_primitive}_indices"})
                    offset += len(primitive.indexed_trilist.vertex_idxs) * 6

                    # align accessor, offset must be multiple of 4
                    while not (offset & 0x03) == 0:
                        bw.write_byte(0)
                        offset += 1

                    prim_state = shape.prim_states[primitive.prim_state_idx]
                    
                    assert prim_state.flags == 0, f"prim_state.flags {prim_state.flags} is not 0."
                    assert prim_state.z_bias == 0, f"prim_state.z_bias {prim_state.z_bias} is not 0."
                    assert prim_state.alpha_test_mode in [0,1], f"prim_state.alpha_test_mode {prim_state.alpha_test_mode} is not 0 or 1."
                    assert prim_state.light_cfg_idx == 0, f"prim_state.light_cfg_idx {prim_state.light_cfg_idx} is not 0."
                    assert prim_state.z_buf_mode == 1, f"prim_state.z_buf_mode {prim_state.z_buf_mode} is not 1."

                    vtx_state = shape.vtx_states[prim_state.i_vtx_state]
                    matrix = shape.matrices[vtx_state.i_matrix]
                    shader = shape.shader_names[prim_state.i_shader]

                    assert shader in ['TexDiff', 'BlendATexDiff'], f"prim_state.i_shader {prim_state.i_shader} is not TexDiff or BlendATexDiff."

                    Logger.log(f"EXTRACT MESH LOD{dlevel}_SUBOBJECT{i_sub_object}_PRIMITIVE{i_primitive} state_name:{prim_state.name} tex_idxs:{prim_state.tex_idxs} i_shader:{prim_state.i_shader} i_vtx_state:{prim_state.i_vtx_state} matrix.name:{matrix.name}")

                    i_node = matrix2node[vtx_state.i_matrix]
                    node = gltf_helper.get_node(i_node)
                    if "mesh" not in node:
                        node["mesh"] = gltf_helper.create_mesh({"primitives": []})

                    alphaMode = ShapeExtractor._get_alphaMode(shader)
                    i_material, material = self._find_material(prim_state.name, prim_state.tex_idxs[0], alphaMode)
                    if i_material != -1:
                        assert material['alphaMode'] == alphaMode, f"material.alphaMode {material['alphaMode']} is not {alphaMode}."
                        assert material['pbrMetallicRoughness']['baseColorTexture']['index'] == prim_state.tex_idxs[0], f"material.pbrMetallicRoughness.baseColorTexture.index {material['pbrMetallicRoughness']['baseColorTexture']['index']} is not {prim_state.tex_idxs[0]}"
                    else:
                        i_material = gltf_helper.create_material({
                            "name" : prim_state.name,
                            "pbrMetallicRoughness": {
                                "baseColorTexture": {
                                    "index": prim_state.tex_idxs[0],
                                    #"texCoord": 1
                                },
                                "metallicFactor": 0.0,
                                "roughnessFactor": 1.0
                            },
                            "alphaMode": alphaMode
                        })

                    i_mesh = node["mesh"]
                    primitives = gltf_helper.get_mesh(i_mesh)["primitives"]
                    primitives.append(
                        {
                            "attributes": {
                                "POSITION": i_accessor_position,
                                "NORMAL": i_accessor_normal,
                                "TEXCOORD_0": i_accessor_texcoord_0
                            },
                            "indices": i_accessor_primitive,
                            "material": i_material,
                            "mode": pliskin.gltf.TRIANGLES
                            #"name": f"{shape_name}_LOD{dlevel}_SUBOBJECT{i_sub_object}_PRIMITIVE{i_primitive}"
                        }
                    )

                end_pos = bw.get_size()
                length = end_pos - start_pos
                gltf_helper.get_buffer(i_buffer)['byteLength'] = bw.get_size()
                gltf_helper.get_bufferView(i_bufferView_element_array)['byteLength'] = length
                gltf_helper.get_bufferView(i_bufferView_element_array)['byteOffset'] = start_pos
            
            # Build node hierarchy
            for i_matrix, i_parent_matrix in enumerate(distance_level.distance_level_header.hierarchy):

                # skip orphaned matrix ? looks like no node was associated to this matrix
                if not i_matrix in matrix2node:
                    continue

                i_node = matrix2node[i_matrix]
                
                # root node must be set in the scene
                if i_parent_matrix == -1:
                    gltf_helper.create_scene({"name": f"LOD{dlevel}", "nodes": [i_node]})
                    continue

                # set the children of the parent
                i_parent_node = matrix2node[i_parent_matrix]
                parent_node = gltf_helper.get_node(i_parent_node)
                if not "children" in parent_node:
                    parent_node["children"] = []

                parent_node["children"].append(i_node)

            # EXTRACT ANIMATION
            self._extract_animations(dlevel, matrix2nodes, bw, i_buffer)

            # print stats
            self.print_stats()

            self._lod_poly_count.append(gltf_helper._triangle_count)

        # CLEANUP & SAVE
        self._cleanup_gltf()
        if self._is3dts(): self._save_3dts_anims() 
        self._save_gltfs_and_buffers()

        Logger.log(f"END.")