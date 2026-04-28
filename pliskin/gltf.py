# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

TRIANGLES = 4

INT16 = 5122
UINT16 = 5123
UINT32 = 5125
FLOAT = 5126

LINEAR = 9729
LINEAR_MIPMAP_NEAREST = 9985
LINEAR_MIPMAP_LINEAR = 9987

REPEAT = 10497 

ARRAY_BUFFER = 34962 # vertex data
ELEMENT_ARRAY_BUFFER = 34963 # indices of vertex data

class GltfHelper:
    def __init__(self, file_name:str):
        self._file_name = file_name
        self._json = {
            "asset": { "version": "2.0" },
            "extensionsUsed": [],
            "extensionsRequired": [],
            "scene": 0,
            "scenes": [],
            "nodes": [],
            "buffers": [],
            "bufferViews": [],
            "accessors": [],
            "images": [],
            "textures": [],
            "materials": [],
            "samplers": [],
            "meshes": [],
            "animations": []
        } 
        self._vertex_count = 0
        self._triangle_count = 0

    def get_dict(self) -> dict:
        return self._json
    
    def get_node(self, i) -> dict:
        return self._json["nodes"][i]
    
    def get_accessor(self, i) -> dict:
        return self._json["accessors"][i]
    
    def get_mesh(self, i) -> dict:
        return self._json["meshes"][i]
    
    def get_scene(self, i) -> dict:
        return self._json["scenes"][i]

    def get_buffer(self, i) -> dict:
        return self._json["buffers"][i]
    
    def get_bufferView(self, i) -> dict:
        return self._json["bufferViews"][i]

    def create_scene(self, scene) -> int:
        self._json["scenes"].append(scene)
        return len(self._json["scenes"])-1

    def create_buffer(self, buffer) -> int:
        self._json["buffers"].append(buffer)
        return len(self._json["buffers"])-1
    
    def create_bufferView(self, bufferView) -> int:
        self._json["bufferViews"].append(bufferView)
        return len(self._json["bufferViews"])-1
    
    def create_accessor(self, accessor) -> int:
        self._json["accessors"].append(accessor)
        return len(self._json["accessors"])-1
    
    def create_image(self, image) -> int:
        self._json["images"].append(image)
        return len(self._json["images"])-1
    
    def create_texture(self, texture) -> int:
        self._json["textures"].append(texture)
        return len(self._json["textures"])-1
    
    def create_sampler(self, sampler) -> int:
        self._json["samplers"].append(sampler)
        return len(self._json["samplers"])-1
    
    def create_mesh(self, mesh) -> int:
        self._json["meshes"].append(mesh)
        return len(self._json["meshes"])-1
    
    def create_node(self, node) -> int:
        self._json["nodes"].append(node)
        return len(self._json["nodes"])-1
    
    def create_material(self, material) -> int:
        self._json["materials"].append(material)
        return len(self._json["materials"])-1
    
    def create_animation(self, animation) -> int:
        if not 'samplers' in animation: animation['samplers'] = []
        if not 'channels' in animation: animation['channels'] = []
        self._json["animations"].append(animation)
        return len(self._json["animations"])-1
    
    def create_animation_channel(self, animation_id, channel) -> int:
        self._json["animations"][animation_id]["channels"].append(channel)
        return len(self._json["animations"][animation_id]["channels"])-1
    
    def create_animation_sampler(self, animation_id, sampler) -> int:
        self._json["animations"][animation_id]["samplers"].append(sampler)
        return len(self._json["animations"][animation_id]["samplers"])-1
    
    def add_extension(self, extension_name:str, required:bool = False) -> None:
        if not extension_name in self._json["extensionsUsed"]:
            self._json["extensionsUsed"].append(extension_name)
        if required and not extension_name in self._json["extensionsRequired"]:
            self._json["extensionsRequired"].append(extension_name)