# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

from msts.TokenId import TokenId
from pliskin.BinaryReader import BinaryReader
from typing import Self
import zlib
from io import BytesIO

class StructuredBlockReader:
    def __init__(self):
        self.id = None
        self.label = None

    def verify_id(self, desired_id: TokenId):
        if (not self.id == desired_id):
            print(f"INFO: Expected block {desired_id}({desired_id.value}); got {self.id}")

    def trace_information(self, string: str):
        print(f"INFO: {string}")

    def trace_warning(self, string: str):
        print(f"WARNING: {string}")

    def trace_error(self, string: str):
        print(f"ERROR: {string}")
    
    @staticmethod
    def Open(filename: str):
        fb = open(filename, 'rb')

        # Test Unicode BOM
        buffer = fb.read(2)
        unicode = (buffer[0] == 0xFF and buffer[1] == 0xFE) # unicode header

        # Read Header
        header_string = None
        if unicode:
            buffer = fb.read(32)
            header_string = buffer[0:16].decode(encoding='utf-16')
        else:
            buffer = bytes(buffer + fb.read(14))
            header_string = buffer[0:8].decode(encoding='ascii')

        #SIMISA@F  means compressed
        #SIMISA@@  means uncompressed
        if header_string.startswith("SIMISA@F"):
            compressed_bytes = fb.read()
            fb.close()
            decompressed_bytes = zlib.decompress(compressed_bytes)
            fb = BytesIO(decompressed_bytes)
        elif header_string.startswith("\r\nSIMISA"):
            # ie us1rd2l1000r10d.s, we are going to allow this but warn
            print(f"WARNING: Improper header in {filename}")
            fb.read(4)
        elif not header_string.startswith("SIMISA@@"):
            raise Exception(f"Unrecognized header \"{header_string}\" in {filename}")
        
        # Read SubHeader
        sub_header = None
        if unicode:
            buffer = fb.read(32)
            sub_header = buffer[0:16].decode(encoding="utf-16")
        else:
            buffer = fb.read(16)
            sub_header = buffer[0:8].decode(encoding='ascii')

        # Select for binary vs text content
        if sub_header[7] == 't':
            raise NotImplementedError("UnicodeFileReader is not implemented.")
            #return new UnicodeFileReader(fb, filename, unicode ? Encoding.Unicode : Encoding.ASCII);
        elif not sub_header[7] == 'b':
            raise Exception(f"Unrecognized subHeader \"{sub_header}\" in {filename}")

        # And for binary types, select where their tokens will appear in our TokenID enum
        if (sub_header[5] == 'w'):   # and [7] must be 'b'
            return BinaryFileReader(fb, filename, 300)
        else:
            return BinaryFileReader(fb, filename, 0)

class BinaryBlockReader(StructuredBlockReader):
    def __init__(self):
        super().__init__()
        self.file_name: str = None
        self.input_stream: BinaryReader = None
        self.remaining_bytes: int = 0
        self.flags: int = 0
        self.token_offset: int = 0

    def read_sub_block(self) -> Self:
        block = BinaryBlockReader()
        block.file_name = self.file_name
        block.input_stream = self.input_stream
        block.token_offset = self.token_offset

        msts_token = self.input_stream.read_uint16()
        block.id = TokenId(msts_token + self.token_offset)
        block.flags = self.input_stream.read_uint16()
        block.remaining_bytes = self.input_stream.read_uint32() # record length

        block_size = block.remaining_bytes + 8 # for the header
        self.remaining_bytes -= block_size

        label_length = self.input_stream.read_byte()
        block.remaining_bytes -= 1
        if label_length > 0:
            buffer = self.input_stream.read_bytes(label_length * 2)
            block.label = buffer.decode("utf-16")
            block.remaining_bytes -= label_length * 2
        return block

    def skip(self):
        if self.remaining_bytes > 0:
            if self.remaining_bytes > 2147483647: #Int32.MaxValue
                self.trace_warning("Remaining Bytes overflow")
                self.remaining_bytes = 1000
                self.input_stream.read_bytes(self.remaining_bytes)
            self.remaining_bytes = 0
        
    def end_of_block(self) -> bool:
        return self.remaining_bytes == 0
    
    def verify_end_of_block(self):
        if not self.end_of_block():
            self.trace_warning(f"Expected end of block {self.id}; got more data")
            self.skip()

    def read_flags(self) -> int:
        self.remaining_bytes -= 4
        return self.input_stream.read_uint32()

    def read_int(self) -> int:
        self.remaining_bytes -= 4
        return self.input_stream.read_int32()

    def read_uint(self) -> int:
        self.remaining_bytes -= 4
        return self.input_stream.read_uint32()
      
    def read_float(self) -> float:
        self.remaining_bytes -= 4
        return self.input_stream.read_single()
    
    def read_string(self) -> str:
        count = self.input_stream.read_uint16()
        if count > 0:
            b = self.input_stream.read_bytes(count * 2)
            s = b.decode("utf-16")
            self.remaining_bytes -= count * 2 + 2
            return s
        else:
            return ""
        
class BinaryFileReader(BinaryBlockReader):
    def __init__(self, input_stream, file_name: str, token_offset: int):
        super().__init__()
        self.input_stream = BinaryReader(input_stream)
        self.file_name = file_name
        self.token_offset = token_offset