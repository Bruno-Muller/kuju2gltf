# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import struct
from io import BytesIO

from PIL import Image
from msts.AceFile import SurfaceFormat


class DdsExtractor:

    @staticmethod
    def build_dds_header(texture, level0_size: int, mip_count: int) -> bytes:
        fourcc_by_format = {
            SurfaceFormat.Dxt1: b"DXT1",
            SurfaceFormat.Dxt3: b"DXT3",
            SurfaceFormat.Dxt5: b"DXT5",
        }

        if texture.surfaceFormat not in fourcc_by_format and texture.surfaceFormat != SurfaceFormat.Color:
            raise NotImplementedError(f"DDS export not implemented for surface format {texture.surfaceFormat}")

        dds_magic = b"DDS "

        # DDS_HEADER
        header_size = 124
        DDSD_CAPS = 0x00000001
        DDSD_HEIGHT = 0x00000002
        DDSD_WIDTH = 0x00000004
        DDSD_PITCH = 0x00000008
        DDSD_PIXELFORMAT = 0x00001000
        DDSD_MIPMAPCOUNT = 0x00020000
        DDSD_LINEARSIZE = 0x00080000

        is_color = texture.surfaceFormat == SurfaceFormat.Color
        flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
        flags |= DDSD_PITCH if is_color else DDSD_LINEARSIZE
        if mip_count > 1:
            flags |= DDSD_MIPMAPCOUNT

        height = texture.height
        width = texture.width
        pitch_or_linear_size = level0_size
        depth = 0
        mip_map_count = mip_count if mip_count > 1 else 0
        reserved1 = [0] * 11

        # DDS_PIXELFORMAT
        pf_size = 32
        DDPF_FOURCC = 0x00000004
        DDPF_RGB = 0x00000040
        DDPF_ALPHAPIXELS = 0x00000001

        if is_color:
            # Ace structured Color stores pixels as 32-bit values with R in lowest byte.
            pf_flags = DDPF_RGB | DDPF_ALPHAPIXELS
            pf_four_cc = b"\x00\x00\x00\x00"
            pf_rgb_bit_count = 32
            pf_r_mask = 0x000000FF
            pf_g_mask = 0x0000FF00
            pf_b_mask = 0x00FF0000
            pf_a_mask = 0xFF000000
        else:
            pf_flags = DDPF_FOURCC
            pf_four_cc = fourcc_by_format[texture.surfaceFormat]
            pf_rgb_bit_count = 0
            pf_r_mask = 0
            pf_g_mask = 0
            pf_b_mask = 0
            pf_a_mask = 0

        # caps
        DDSCAPS_COMPLEX = 0x00000008
        DDSCAPS_TEXTURE = 0x00001000
        DDSCAPS_MIPMAP = 0x00400000
        caps = DDSCAPS_TEXTURE | (DDSCAPS_COMPLEX | DDSCAPS_MIPMAP if mip_count > 1 else 0)
        caps2 = 0
        caps3 = 0
        caps4 = 0
        reserved2 = 0

        header = struct.pack(
            "<4sI I I I I I I 11I I I 4s I I I I I I I I I I",
            dds_magic,
            header_size,
            flags,
            height,
            width,
            pitch_or_linear_size,
            depth,
            mip_map_count,
            *reserved1,
            pf_size,
            pf_flags,
            pf_four_cc,
            pf_rgb_bit_count,
            pf_r_mask,
            pf_g_mask,
            pf_b_mask,
            pf_a_mask,
            caps,
            caps2,
            caps3,
            caps4,
            reserved2,
        )

        return header

    @staticmethod
    def dds_to_image(dds_filename: str) -> Image.Image:
        with open(dds_filename, "rb") as f:
            data = f.read()
        assert data[0:4] == b"DDS ", f"Not a DDS file: {dds_filename}"

        height     = struct.unpack_from("<I", data, 12)[0]
        width      = struct.unpack_from("<I", data, 16)[0]
        pf_flags   = struct.unpack_from("<I", data, 80)[0]
        pf_four_cc = data[84:88]
        pixel_data = data[128:]

        DDPF_FOURCC = 0x00000004
        if pf_flags & DDPF_FOURCC:
            if pf_four_cc == b"DXT1":
                buffer = Dxt1Extractor.extract_dxt1(BytesIO(pixel_data), width, height)
                return Image.frombuffer("RGBA", (width, height), buffer)
            else:
                raise NotImplementedError(f"DDS FourCC {pf_four_cc!r} not supported for PNG conversion")
        else:
            # ARGB: 32-bit little-endian packed pixels
            colors = struct.unpack_from(f"<{width * height}I", pixel_data)
            buf = bytearray(4 * width * height)
            for idx, color in enumerate(colors):
                i = idx * 4
                buf[i+0] = (color >>  0) & 0xFF  # R
                buf[i+1] = (color >>  8) & 0xFF  # G
                buf[i+2] = (color >> 16) & 0xFF  # B
                buf[i+3] = (color >> 24) & 0xFF  # A
            return Image.frombuffer("RGBA", (width, height), bytes(buf))


class Dxt1Extractor:
    @staticmethod
    def extract_dxt1(data:bytes, width:int, height:int, precomp_alpha:float = 1.0) -> bytes:
        def _clamp(val:int, v_min:int, v_max:int) -> int:
            return int(min(max((val), v_min), v_max))

        def _decode565(bits:int) -> tuple[int, int, int]:
            a = ((bits >> 11) & 0x1F) << 3
            b = ((bits >> 5) & 0x3F) << 2
            c = (bits & 0x1F) << 3
            return a, b, c

        def _c2a(a:int, b:int) -> int:
            return (2 * a + b) // 3

        def _c2b(a:int, b:int) -> int:
            return (a + b) // 2

        def _c3(a:int, b:int) -> int:
            return (2 * b + a) // 3

        buffer = bytearray(4 * width * height)
        alpha = _clamp(precomp_alpha * 255, 0, 255)

        for y in range(0, height, 4):
            for x in range(0, width, 4):
                color0, color1, bits = struct.unpack("<HHI", data.read(8))

                r0, g0, b0 = _decode565(color0)
                r1, g1, b1 = _decode565(color1)

                # Decode this block into 4x4 pixels
                for j in range(4):
                    for i in range(4):
                        # get next control op and generate a pixel
                        control = bits & 3
                        bits = bits >> 2
                        if control == 0:
                            r, g, b, a = r0, g0, b0, alpha
                        elif control == 1:
                            r, g, b, a = r1, g1, b1, alpha
                        elif control == 2:
                            if color0 > color1:
                                r, g, b, a = _c2a(r0, r1), _c2a(g0, g1), _c2a(b0, b1), alpha
                            else:
                                r, g, b, a = _c2b(r0, r1), _c2b(g0, g1), _c2b(b0, b1), alpha
                        elif control == 3:
                            if color0 > color1:
                                r, g, b, a = _c3(r0, r1), _c3(g0, g1), _c3(b0, b1), alpha
                            else:
                                r, g, b, a = 0, 0, 0, 0

                        idx = 4 * ((y + j) * width + x + i)
                        buffer[idx : idx + 4] = struct.pack("4B", r, g, b, a)

        return bytes(buffer)