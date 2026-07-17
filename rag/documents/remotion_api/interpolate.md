# Remotion: useCurrentFrame and interpolate

These two hooks are the core of Remotion animations.

## useCurrentFrame

Returns the current frame number (0-indexed) on every render.

```tsx
import { useCurrentFrame } from 'remotion';

const MyComponent: React.FC = () => {
  const frame = useCurrentFrame();
  return <div>Current frame: {frame}</div>;
};
```

## interpolate

Maps a frame number to an output value using a defined input and output range.

```tsx
import { interpolate, useCurrentFrame } from 'remotion';

const opacity = interpolate(
  frame,
  [0, 30],     // input range: frames 0–30
  [0, 1],      // output range: 0 → 1 (fade in over 1 second at 30fps)
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);
```

## Common use cases

### Fade in
```tsx
const opacity = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });
```

### Fade out (given component starts at frame `from` and lasts `duration` frames)
```tsx
const frame = useCurrentFrame();
const opacity = interpolate(
  frame,
  [duration - 20, duration],
  [1, 0],
  { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
);
```

### Ken Burns (slow zoom)
```tsx
const scale = interpolate(frame, [0, durationFrames], [1, 1.08], { extrapolateRight: 'clamp' });
const style = { transform: `scale(${scale})`, transformOrigin: 'center center' };
```

### Slide in from right
```tsx
const translateX = interpolate(frame, [0, 20], [100, 0], { extrapolateRight: 'clamp' });
const style = { transform: `translateX(${translateX}%)` };
```

## Common error: missing extrapolateRight clamp
Without `{ extrapolateRight: 'clamp' }`, values will continue extrapolating beyond the defined range, causing visual glitches.
