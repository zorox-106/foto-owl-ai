# Remotion: AbsoluteFill and spring

## AbsoluteFill

Shorthand for `<div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}>`.

```tsx
import { AbsoluteFill } from 'remotion';

<AbsoluteFill style={{ backgroundColor: '#000' }}>
  {/* Full-frame children */}
</AbsoluteFill>
```

Use as the outermost element of every composition and scene component.

## spring

`spring` generates a physically-based eased animation value.

```tsx
import { spring, useCurrentFrame, useVideoConfig } from 'remotion';

const frame = useCurrentFrame();
const { fps } = useVideoConfig();

// Bouncy entrance animation
const scale = spring({
  frame,
  fps,
  config: {
    damping: 15,  // higher = less bounce
    stiffness: 80,
    mass: 1,
  },
  from: 0,
  to: 1,
});
```

### spring with delay
```tsx
const opacity = spring({
  frame: Math.max(0, frame - 15),  // delay by 15 frames
  fps,
  config: { damping: 20 },
  from: 0,
  to: 1,
});
```

## Caption overlay using AbsoluteFill

```tsx
<AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 60 }}>
  <div
    style={{
      color: 'white',
      fontSize: 42,
      fontFamily: 'sans-serif',
      textShadow: '0 2px 8px rgba(0,0,0,0.8)',
      opacity: interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' }),
    }}
  >
    {caption}
  </div>
</AbsoluteFill>
```

## Common error: caption not visible
If the caption `AbsoluteFill` is rendered before the image `AbsoluteFill`, it will be hidden behind the image. Always put overlays AFTER content in JSX order.
