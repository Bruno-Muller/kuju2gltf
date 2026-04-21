# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import struct

from msts.AceFile import SurfaceFormat


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
