# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 Bruno Muller
# https://polyformproject.org/licenses/noncommercial/1.0.0

import argparse
from shape_extractor import ShapeExtractor
import main_window

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
        epilog="It's-a-me, Mario! https://github.com/Bruno-Muller/kuju2gltf"
    )
    
    parser.add_argument('input_file', nargs='?', default='', help="Input, Kuju Shape file (.s)")
    parser.add_argument('output_dir', nargs='?', default='', help="Output, directory")
    parser.add_argument(
        '-format',
        choices=['3dts', 'orts'],
        required=False,
        help="Output format: '3dts' for 3D Train Studio, 'orts' for Open Rails"
    )
    parser.add_argument(
        '-nogui',
        action='store_true',
        help="Run in command-line mode (no GUI)"
    )
    args = parser.parse_args()

    if args.nogui:
        extractor = ShapeExtractor(args.input_file, args.output_dir, args.format)
        extractor.run()
    else:
        main_window.main(input_file=args.input_file, output_dir=args.output_dir)