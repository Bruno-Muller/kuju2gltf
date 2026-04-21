## About this project

This project was originally designed to export MSTS/ORTS shapes (`.s` format) to **3D Train Studio** (`.gltf`), with `.ace` textures converted to `.png`. This initial implementation was hand written by the repository owner.

Support for exporting to **OpenRails** (`.gltf` with `MSFT_texture_dds` extension), with `.ace` textures converted to `.dds`, was added later with help of Artificial Intelligence.

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).  
Free to use, modify, and distribute for non-commercial purposes only.

## Examples

### OpenRails
```bash
kuju2gltf "C:\path\to\shape.s" "C:\path\to\outputdir" -format orts
```

### 3D Train Studio
```bash
kuju2gltf "C:\path\to\shape.s" "C:\path\to\outputdir" -format 3dts
```

## Important note

The `.s` file must be in binary format.

If your shape is a Unicode text shape, convert it to binary first with `ffeditc_unicode.exe` (provided with MSTS).

## Compatibility

### Export to 3D Train Studio
| Feature | Support |
|---|---|
| Animations | ✅ Supported |
| LODs | ✅ Supported |

### Export to OpenRails

> Reference: [OpenRails documentation — 3D Shape Files](https://open-rails.readthedocs.io/en/unstable/developing.html#d-shape-files)

| Feature | Support |
|---|---|
| `MSFT_texture_dds` extension | ✅ Supported |
| LOD | ⚠️ Untested — LODs are generated as individual files and should be compatible |
| `MSFT_lod` extension | ❌ Not supported |
| `KHR_lights_punctual` extension | ❌ Not supported |

## Supported Texture Formats

| ACE format (in) | PNG (out) | DDS (out) | Notes |
|---|---|---|---|
| `Color` (ARGB 32 bits) | ✅ | ✅ | DDS no compression (32 bits with 8-bits alpha channel) |
| `Dxt1` | ✅ | ✅ | DDS compression `DXT1` (can include 1-bit alpha mask) |
| `Dxt3` | ❌ | ✅ | DDS compression `DXT3` |
| `Dxt5` | ❌ | ✅ | DDS compression `DXT5` |
| `Bgr565` | ❌ | ❌ | Not Implemented |
| `Bgra5551` | ❌ | ❌ | Not Implemented |
| `Bgra4444` | ❌ | ❌ | Not Implemented |