# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

from PIL import Image
from dxt_extractor import DxtExtractor, DdsExtractor
from msts.AceFile import *
from pliskin.logger import Logger
import struct
import shutil

class TextureExtractor:

    def __init__(self, output_dir:str):
        self._output_dir = output_dir

    @staticmethod
    def _extract_argb(data:bytes, width:int, height:int) -> bytes:
        buffer = bytearray(4 * width * height)
        i = 0
        for color in data:
            buffer[i+0] = (color >> 0) & 0x0FF # R
            buffer[i+1] = (color >> 8) & 0x0FF # G
            buffer[i+2] = (color >> 16) & 0x0FF # B
            buffer[i+3] = (color >> 24) & 0x0FF # A
            i += 4
        return bytes(buffer)

    @staticmethod
    def _texture_to_image(texture: Texture2D, level = 0) -> Image.Image:
        level_data = texture.levels[level]
        height = texture.height>>level
        width = texture.width>>level
        print(f"level:{level} {width}x{height}")
        
        if texture.surfaceFormat == SurfaceFormat.Color:
            #ARGB
            Logger.log("ARGB")
            buffer =  TextureExtractor._extract_argb(level_data, width, height)
            return Image.frombuffer("RGBA", (width, height), buffer)

        elif texture.surfaceFormat == SurfaceFormat.Dxt1:
            Logger.log("Dxt1")
            buffer = DxtExtractor.extract_dxt1(BytesIO(level_data), width, height)
            return Image.frombuffer("RGBA", (width, height), buffer)

        elif texture.surfaceFormat == SurfaceFormat.Dxt3:
            Logger.log("Dxt3")
            buffer = DxtExtractor.extract_dxt3(BytesIO(level_data), width, height)
            return Image.frombuffer("RGBA", (width, height), buffer)

        elif texture.surfaceFormat == SurfaceFormat.Dxt5:
            Logger.log("Dxt5")
            buffer = DxtExtractor.extract_dxt5(BytesIO(level_data), width, height)
            return Image.frombuffer("RGBA", (width, height), buffer)

        else:
            raise NotImplementedError(f"Not implemented {texture.surfaceFormat}")

    def save_ace2png(self, source_filename : str, overwrite:bool = False) -> AceInfo:
        assert source_filename.lower().endswith(".ace")

        file_name = os.path.basename(source_filename)
        png_filename = os.path.join(self._output_dir, file_name)[:-4] + ".png"

        texture = AceFile.Texture2DFromFile(source_filename)
        #print(f"{image} mipMap:{len(texture.levels)} surfaceFormat:{texture.surfaceFormat}")

        if not overwrite and os.path.exists(png_filename):
            Logger.log(f"skip existing extracted file, \"{source_filename}\" → \"{png_filename}\"")
            
        else:
            Logger.log(f"extract file, \"{source_filename}\" → \"{png_filename}\"")
            im = TextureExtractor._texture_to_image(texture)
            im.save(png_filename)

        return texture.Tag
        
    def save_dds2png(self, source_filename : str, overwrite:bool = False) -> AceInfo:
        assert source_filename.lower().endswith(".dds")

        file_name = os.path.basename(source_filename)
        png_filename = os.path.join(self._output_dir, file_name)[:-4] + ".png"
        
        im, dds_format  = DdsExtractor.dds_to_image(source_filename)

        if not overwrite and os.path.exists(png_filename):
            Logger.log(f"skip existing extracted file, \"{source_filename}\" → \"{png_filename}\"")
        else:
            Logger.log(f"extract file, \"{source_filename}\" → \"{png_filename}\"")
            im.save(png_filename)

        ace_info = AceInfo()
        ace_info.alphaBits = DdsExtractor.get_alpha_bits(dds_format)
        return ace_info
    
    def copy_dds2dds(self, source_filename : str, overwrite:bool = False) -> AceInfo:
        assert source_filename.lower().endswith(".dds")

        file_name = os.path.basename(source_filename)
        dds_filename = os.path.join(self._output_dir, file_name)[:-4] + ".dds"

        im, dds_format  = DdsExtractor.dds_to_image(source_filename)

        if not overwrite and os.path.exists(dds_filename):
            Logger.log(f"skip existing extracted file, \"{source_filename}\" → \"{dds_filename}\"")
        else:
            Logger.log(f"copy file, \"{source_filename}\" → \"{dds_filename}\"")
            shutil.copy2(source_filename, dds_filename)
        
        ace_info = AceInfo()
        ace_info.alphaBits = DdsExtractor.get_alpha_bits(dds_format)
        return ace_info
        
    def save_ace2dds(self, source_filename : str, overwrite:bool = False) -> AceInfo:
        assert source_filename.lower().endswith(".ace")
        file_name = os.path.basename(source_filename)
        dds_filename = os.path.join(self._output_dir, file_name)[:-4] + ".dds"

        texture = AceFile.Texture2DFromFile(source_filename)
        
        if not overwrite and os.path.exists(dds_filename):
            Logger.log(f"skip existing extracted file, \"{source_filename}\" → \"{dds_filename}\"")

        else:
            Logger.log(f"extract file, \"{source_filename}\" → \"{dds_filename}\"")

            levels = [texture.levels[i] for i in sorted(texture.levels.keys())]
            if len(levels) == 0:
                raise ValueError(f"No texture payload found in {source_filename}")

            if texture.surfaceFormat == SurfaceFormat.Color:
                level0_size = texture.width * 4
            else:
                level0_size = len(levels[0])

            header = DdsExtractor.build_dds_header(texture, level0_size, len(levels))
            with open(dds_filename, "wb") as f:
                f.write(header)
                for level_data in levels:
                    if texture.surfaceFormat == SurfaceFormat.Color:
                        f.write(struct.pack(f"<{len(level_data)}I", *level_data))
                    else:
                        f.write(level_data)

        return texture.Tag