## About this project

This project was originally designed to export MSTS/ORTS shapes (`.s` format) to **3D Train Studio** (`.gltf`), with `.ace` textures converted to `.png`. This initial implementation was hand written by the repository owner.

Support for exporting to **OpenRails** (`.gltf` with `MSFT_texture_dds` extension), with `.ace` textures converted to `.dds`, was added later with help of Artificial Intelligence.

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).  
Free to use, modify, and distribute for non-commercial purposes only.

## How to use

### Graphical interface (GUI)

Launch `kuju2gltf` without arguments to open the graphical interface.

- **Drag & drop** one or more source files onto the input box, or click **Browse…** to select them.
- **Drag & drop** the output folder onto the output field, or click **Browse…** to pick a directory.
- Click **Convert**.

Supported conversions from the GUI:

| Source | Output |
|---|---|
| `.s` (MSTS shape) | `.gltf` |
| `.ace` (MSTS texture) | `.png` + `.dds` |
| `.dds` | `.png` |

Multiple source files can be queued at once — they are converted sequentially.

### Command-line (CLI)

> Add `-nogui` to bypass the graphical interface.

#### OpenRails
```bash
kuju2gltf "C:\path\to\shape.s" "C:\path\to\outputdir" -format orts -nogui
```

#### 3D Train Studio
```bash
kuju2gltf "C:\path\to\shape.s" "C:\path\to\outputdir" -format 3dts -nogui
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

| Feature | Support | Notes |
|---|---|---|
| `MSFT_texture_dds` extension | ✅ | |
| LOD | ✅ | LODs are generated as individual files |
| `MSFT_lod` extension | ❌ | |
| `KHR_lights_punctual` extension | ❌ | |

## Supported Texture Formats

| ACE (in) | PNG (out) | DDS (out) | Notes |
|---|---|---|---|
| `Color` (ARGB 32 bits) | ✅ `RGBA` | ✅ `A8B8G8R8` | 32 bits with 8-bits alpha channel |
| `Dxt1` | ✅ `RGBA` | ✅ `Dxt1` | can include 1-bit alpha mask |
| `Dxt3` | ✅ `RGBA` | ✅ `Dxt3` | 4-bits alpha mask |
| `Dxt5` | ✅ `RGBA` | ✅ `Dxt5` | 4-bits alpha mask |

| DDS (in) | PNG (out) | DDS (out) | Notes |
|---|---|---|---|
| `A8R8G8B8` <br> `A8B8G8R8` | ✅ `RGBA` | ✅ | 32 bits with 8-bits alpha channel |
| `Dxt1` | ✅ `RGBA` | ✅ | can include 1-bit alpha mask |
| `Dxt3` | ✅ `RGBA` | ✅ | 4-bits alpha mask |
| `Dxt5` | ✅ `RGBA` | ✅ | 4-bits alpha mask |

Note: PNG files are in 32-bit RGBA format (8 bits per channel, including alpha).

Note: DDS (in) to DDS (out) is a straight copy with no conversion.

## Supported Texture Filters

| Filter (in) | Sampler.magFilter (out) | Sampler.minFilter (out) |
|---|---|---|
| `Linear` | `LINEAR` (9729) | `LINEAR` (9729) |
| `MipLinear` | `LINEAR` (9729) | `LINEAR_MIPMAP_NEAREST` (9985) |
| `LinearMipLinear` | `LINEAR` (9729) | `LINEAR_MIPMAP_LINEAR` (9987) |

Note: if the texture is not provided/not found then the Blending mode (`OPAQUE` or `MASK`) cannot be determined during conversion and will default to `OPAQUE`.

Note: About shape .s Texture definition; `mip_map_lod_bias` in .s has no equivalent in .glTF and information is lost in glTF.

Note: About shape .s Primitive State definition; `z_buf_mode` and `z_bias` are ingored and information is lost in glTF.