# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import struct

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