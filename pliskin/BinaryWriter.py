# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import struct 
from io import BufferedWriter, BytesIO

class BinaryWriter:
    def __init__(self, output_stream: BufferedWriter):
        self.output_stream = output_stream

    def write_bytes(self, buffer: bytes) -> None:
        return self.output_stream.write(buffer)

    def write_byte(self, value: int) -> None:
        self.output_stream.write(struct.pack('B', value))

    def write_uint16(self, value: int) -> None:
        self.output_stream.write(struct.pack('H', value))

    def write_int16(self, value: int) -> None:
        self.output_stream.write(struct.pack('h', value))

    def write_uint32(self, value: int) -> None:
        self.output_stream.write(struct.pack('I', value))

    def write_int32(self, value: int) -> None:
        self.output_stream.write(struct.pack('i', value))
    
    def write_uint64(self, value: float) -> None:
        self.output_stream.write(struct.pack('Q', value))

    def write_single(self, value: float) -> None:
        self.output_stream.write(struct.pack('f', value))
    
    def get_size(self) -> int:
        return self.output_stream.seek(0,1)
    
    def get_bytes(self) -> bytes:
        if isinstance(self.output_stream, BytesIO):
            return self.output_stream.getvalue()
        raise Exception("Unsupported operation, BufferedWriter is not instance of BytesIO")
    
    def seek(self, target:int, whence:int=0) -> int:
        return self.output_stream.seek(target, whence)

