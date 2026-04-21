# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import argparse
from shape_extractor import ShapeExtractor

if __name__ == '__main__':
    
    # GLTF
    # https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#_animation_channel_target_path

    # https://3d-train-studio.uk/concepts/
    # see notes, Optimisation on LOD and materials

    # Open Rails
    # https://open-rails.readthedocs.io/en/unstable/developing.html#d-shape-files

    parser = argparse.ArgumentParser(
        prog='kuju2gltf',
        description='This program converts from Kuju\'s format Shape file \".s\" and associated Texture file \".ace\" to glTF format.',
        epilog="https://github.com/Bruno-Muller/kuju2gltf\n\nIt's-a-me, Mario!"
    )
    
    parser.add_argument('input_file', help="Input, Kuju Shape file (.s)") 
    parser.add_argument('output_dir', help="Output, directory")
    parser.add_argument(
        '-format',
        choices=['3dts', 'orts'],
        required=False,
        help="Output format: '3dts' for 3D Train Studio, 'orts' for Open Rails"
    )
    args = parser.parse_args()
    
    extractor = ShapeExtractor(args.input_file, args.output_dir, args.format)
    extractor.run()