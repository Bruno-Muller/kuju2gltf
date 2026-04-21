# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import struct 
from io import BufferedReader

class BinaryReader:
    def __init__(self, input_stream: BufferedReader):
        self.input_stream = input_stream

    def read_bytes(self, count: int) -> bytes:
        return self.input_stream.read(count)

    def read_byte(self) -> int:
        return struct.unpack('B', self.input_stream.read(1))[0]

    def read_uint16(self) -> int:
        return struct.unpack('H', self.input_stream.read(2))[0]
    
    def read_int16(self) -> int:
        return struct.unpack('h', self.input_stream.read(2))[0]
    
    def read_uint32(self) -> int:
        return struct.unpack('I', self.input_stream.read(4))[0]
    
    def read_int32(self) -> int:
        return struct.unpack('i', self.input_stream.read(4))[0]
    
    def read_uint64(self) -> int:
        return struct.unpack('Q', self.input_stream.read(8))[0]
    
    def read_single(self) -> float:
        return struct.unpack('f', self.input_stream.read(4))[0]
    
    def seek(self, target:int, whence:int = 0) -> int:
        return self.input_stream.seek(target, whence)