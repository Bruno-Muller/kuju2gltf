# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

from typing_extensions import Self
from io import BufferedReader
from pliskin.BinaryReader import BinaryReader
import zlib
from io import BytesIO
import os
from enum import IntEnum, Enum, auto
import math
from typing import List

class AceInfo:
    alphaBits = 0

# SurfaceFormat is XNA
class SurfaceFormat(Enum):
    Color = auto()
    Bgr565 = auto()
    Bgra5551 = auto()
    Bgra4444 = auto()
    Dxt1 = auto()
    Dxt3 = auto()
    Dxt5 = auto()

class SimisAceFormatOptions(IntEnum):
    Default : int = 0
    MipMaps : int = 0x01
    RawData : int = 0x10

class SimisAceChannelId(IntEnum):
    Mask = 2
    Red = 3
    Green = 4
    Blue = 5
    Alpha = 6

    def __str__(self):
        if self == SimisAceChannelId.Mask: return "Mask"
        if self == SimisAceChannelId.Red: return "Red"
        if self == SimisAceChannelId.Green: return "Green"
        if self == SimisAceChannelId.Blue: return "Blue"
        if self == SimisAceChannelId.Alpha: return "Alpha"

class SimisAceChannel:
    size : int = 0
    type : SimisAceChannelId = 0

    def __init__(self : Self, size: int, type: SimisAceChannelId):
        self.size = size
        self.type = type

# Texture2D is XNA
class Texture2D:
    def __init__(self, width: int, height:int , hasMipMap:bool, surfaceFormat: SurfaceFormat):
        self.width = width
        self.height = height
        self.hasMipMap = hasMipMap
        self.surfaceFormat = surfaceFormat
        self.levels = dict()
        print(f"Texture2D.__init__: {width}x{height} mipMap:{hasMipMap} surfaceFormat:{surfaceFormat}")

    def set_data(self, level: int, rectangle, data: bytes, startIndex: int, elementCount: int):
        #if len(self.levels) <= level:
        #    self.levels.append(None)
        endIndex = elementCount-startIndex
        self.levels[level] = data[startIndex:endIndex]
        print(f"Texture2D.set_data: level:{level}, startIndex:{startIndex}, elementCount:{elementCount} len:{len(self.levels[level])}")


class AceFile:   

    @staticmethod
    def Texture2DFromReader(reader: BinaryReader) -> Texture2D:
        # This is a mapping between the 'surface format' found in ACE files and XNA's enum.
        #@staticmethod
        SimisAceSurfaceFormats = {
            0x0E: SurfaceFormat.Bgr565,
            0x10: SurfaceFormat.Bgra5551,
            0x11: SurfaceFormat.Bgra4444,
            0x12: SurfaceFormat.Dxt1,
            0x14: SurfaceFormat.Dxt3,
            0x16: SurfaceFormat.Dxt5
        }

        signature = reader.read_bytes(4)
        if not signature == b"\x01\x00\x00\x00":
            raise Exception("Incorrect signature; expected '01 00 00 00', got '{signature}'")#, StringToHex(signature)));
        options = reader.read_int32() # var options = (SimisAceFormatOptions)reader.ReadInt32();
        width = reader.read_int32()
        height = reader.read_int32()
        surfaceFormat = reader.read_int32()
        channelCount = reader.read_int32()
        reader.read_bytes(128) # Miscellaneous other data we don't care about.

        # If there are mipmaps, we must validate that the image is square and dimensions are an integral power-of-two.
        if (options & SimisAceFormatOptions.MipMaps) != 0:
            if (width != height):
               raise  Exception(f"Dimensions must match when mipmaps are used; got {width}x{height}")
            if (width == 0 or (width & (width - 1)) != 0):
                raise Exception(f"Width must be an integral power of 2 when mipmaps are used; got {width}")
            if (height == 0 or (height & (height - 1)) != 0):
                raise Exception(f"Height must be an integral power of 2 when mipmaps are used; got {height}")

        # If the data is raw data, we must be able to convert the Ace format in to an XNA format or we'll blow up.
        textureFormat = SurfaceFormat.Color
        if ((options & SimisAceFormatOptions.RawData) != 0):
            if not surfaceFormat in SimisAceSurfaceFormats:
                raise Exception(f"Unsupported surface format {surfaceFormat:X8}")
            textureFormat = SimisAceSurfaceFormats[surfaceFormat]

        # Calculate how many images we're going to load; 1 for non-mipmapped, 1+log(width)/log(2) for mipmapped.
        imageCount = 1 + (int(math.log(width) / math.log(2)) if (options & SimisAceFormatOptions.MipMaps) != 0 else 0)
        texture = None
        if ((options & SimisAceFormatOptions.MipMaps) == 0):
            texture = Texture2D(width, height, False, textureFormat)
        else:
            texture = Texture2D(width, height, True, textureFormat)

        # Read in the color channels; each one defines a size (in bits) and type (reg, green, blue, mask, alpha).
        channels: List[SimisAceChannel] = []
        for channel in range(0, channelCount):
            size = reader.read_uint64()
            if ((size != 1) and (size != 8)):
                raise Exception(f"Unsupported color channel size {size}")
            type = reader.read_uint64()
            if ((type < 2) or (type > 6)):
                raise Exception(f"Unknown color channel type {type}")
            channels.append(SimisAceChannel(size, type))
            print(f"channel:{channel} size {size} type {SimisAceChannelId(type)}")

        # Construct some info about this texture for the game to use in optimisations.
        aceInfo = AceInfo()
        texture.Tag = aceInfo
        if any(item.type == SimisAceChannelId.Alpha for item in channels):
            aceInfo.alphaBits = 8
        elif any(item.type == SimisAceChannelId.Mask for item in channels):
            aceInfo.alphaBits = 1
        print(f"alphaBits:{aceInfo.alphaBits}")

        if ((options & SimisAceFormatOptions.RawData) != 0):
            print("RAW")
            # Raw data is stored as a table of 32bit int offsets to each mipmap level.
            reader.read_bytes(imageCount * 4)

            buffer = bytearray(0)
            for imageIndex in range(0, imageCount):
                imageWidth = width // math.pow(2, imageIndex)
                imageHeight = height // math.pow(2, imageIndex)

                # If the mipmap level is width>=4, it is stored as raw data with a 32bit int length header.
                # Otherwise, it is stored as a 32bit ARGB block.
                if (imageWidth >= 4 and imageHeight >= 4):
                    buffer = reader.read_bytes(reader.read_int32())

                # For <4 pixels the images are in RGB format. There's no point reading them though, as the
                # API accepts the 4x4 image's data for the 2x2 and 1x1 case. They do need to be set though!

                texture.set_data(imageIndex, None, buffer, 0, len(buffer))
        else:
            print("Structured data")
            # Structured data is stored as a table of 32bit offsets to each scanline of each image.
            for imageIndex in range(0, imageCount):
                reader.read_bytes(4 * height // int(math.pow(2, imageIndex)))

            buffer = [0] * (width * height)
            channelBuffers = [None] * 8
            for imageIndex in range(0, imageCount):
                imageWidth = width // int(math.pow(2, imageIndex))
                imageHeight = height // int(math.pow(2, imageIndex))
                for y in range(0, imageHeight):
                    for channel in channels:
                        if (channel.size == 1):
                            # 1bpp channels start with the MSB and work down to LSB and then the next byte.
                            bytes = reader.read_bytes(math.ceil(channel.size * imageWidth / 8))
                            channelBuffers[int(channel.type)] = bytearray(imageWidth)
                            for x in range (0, imageWidth):
                                channelBuffers[int(channel.type)][x] = (((bytes[x // 8] >> (7 - (x % 8))) & 1) * 0x0FF)
                        else:
                            # 8bpp are simple.
                            channelBuffers[int(channel.type)] = reader.read_bytes(imageWidth)
                    
                    for x in range(0, imageWidth):
                        buffer[imageWidth * y + x] = channelBuffers[SimisAceChannelId.Red][x] + (channelBuffers[SimisAceChannelId.Green][x] << 8) + (channelBuffers[SimisAceChannelId.Blue][x] << 16)

                        if (channelBuffers[SimisAceChannelId.Alpha] != None):
                            buffer[imageWidth * y + x] += channelBuffers[SimisAceChannelId.Alpha][x] << 24
                        elif (channelBuffers[SimisAceChannelId.Mask] != None):
                            buffer[imageWidth * y + x] += channelBuffers[SimisAceChannelId.Mask][x] << 24
                        else:
                            buffer[imageWidth * y + x] += (0x0FF << 24)
                texture.set_data(imageIndex, None, buffer, 0, imageWidth * imageHeight)
        return texture


    @staticmethod
    def Texture2DFromStream(stream: BufferedReader) -> Texture2D:
        #using (var reader = new BinaryReader(stream, ByteEncoding.Encoding))
        reader = BinaryReader(stream)
        signature = reader.read_bytes(8).decode(encoding='ascii')

        if signature == "SIMISA@F":
            # Compressed header has the uncompressed size embedded in the @-padding.
            reader.read_uint32()
            signature = reader.read_bytes(4).decode(encoding='ascii')
            if not signature == "@@@@":
                raise Exception(f"Incorrect signature; expected '@@@@', got '{signature}'")
                                
            # The stream is technically ZLIB, but we assume the selected ZLIB compression is DEFLATE (though we verify that here just in case). The ZLIB header for DEFLATE is 0x78 0x9C.
            zlib_header = reader.read_uint16()
            if (not (zlib_header & 0x20FF) == 0x0078):
                raise Exception(f"Incorrect signature; expected 'xx78', got '{zlib_header:X4}'")
            stream.seek(-2, os.SEEK_CUR)

            # The BufferedInMemoryStream is needed because DeflateStream only supports reading forwards - no seeking.
            compressed_bytes = stream.read()
            stream.close()
            decompressed_bytes = zlib.decompress(compressed_bytes)
            stream = BytesIO(decompressed_bytes)
            reader = BinaryReader(stream)
            return AceFile.Texture2DFromReader(reader)
            #return Texture2DFromReader(graphicsDevice, new BinaryReader(new BufferedInMemoryStream(new DeflateStream(stream, CompressionMode.Decompress))));
 
        elif signature == "SIMISA@@":
            # Uncompressed header is all @-padding.
            signature = reader.read_bytes(8).decode(encoding='ascii')
            if not signature == "@@@@@@@@":
                raise Exception(f"Incorrect signature; expected '@@@@@@@@', got '{signature}'")

            # Start reading the texture from the same reader.
            return AceFile.Texture2DFromReader(reader)
        else:
            raise Exception(f"Incorrect signature; expected 'SIMISA@F' or 'SIMISA@@', got '{signature}'")
    
    @staticmethod
    def Texture2DFromFile(file_name: str) -> Texture2D:
        with open(file_name, 'rb') as stream:
            return AceFile.Texture2DFromStream(stream)



 