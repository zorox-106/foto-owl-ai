# Remotion: Img and staticFile

## Img component

Use Remotion's `<Img>` (not `<img>`) to load images in compositions. Remotion's `<Img>` handles preloading correctly during rendering.

```tsx
import { Img, staticFile } from 'remotion';

// Correct usage
<Img src={staticFile('photos/wedding_01.jpg')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />

// Wrong — do not use plain HTML <img>
<img src="./photos/wedding_01.jpg" />  // ❌ will not preload correctly
```

## staticFile

Maps a filename to a resolved URL pointing to the `public/` directory of the Remotion project.

```tsx
import { staticFile } from 'remotion';

const src = staticFile('photos/DSC_4491.jpg');
// resolves to: /photos/DSC_4491.jpg (served from public/photos/)
```

## Absolute filesystem paths in staticFile

⚠️ `staticFile` does NOT accept absolute filesystem paths. Files must be placed inside the `public/` directory of the Remotion project and referenced by their relative path within `public/`.

```ts
// ❌ Wrong — absolute path will not work
staticFile('/Users/rajattiwari/Desktop/foto-owl-ai/AHD_6008.jpg')

// ✅ Correct — copy the file to public/ first, then reference it
staticFile('AHD_6008.jpg')  // file is at remotion/public/AHD_6008.jpg
```

## objectFit for full-screen images

```tsx
<Img
  src={staticFile(fileName)}
  style={{
    width: '100%',
    height: '100%',
    objectFit: 'cover',   // 'cover' fills the frame; 'contain' letterboxes
    objectPosition: 'center',
  }}
/>
```

## Common error: image not found
If the file is missing from `public/`, Remotion will throw during render. Always verify the file is in `public/` before generating the script.
