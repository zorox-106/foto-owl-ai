# Remotion: Sequence

`<Sequence>` renders its children only during a specified frame range.

## Signature

```tsx
import { Sequence } from 'remotion';

<Sequence from={startFrame} durationInFrames={durationFrames}>
  {/* children only render when currentFrame is in [from, from + durationInFrames) */}
  <MyScene />
</Sequence>
```

## Key props
- `from`: Frame at which this sequence starts (0-indexed)
- `durationInFrames`: How many frames this sequence lasts
- `layout`: Optional — `'absolute-fill'` (default) or `'none'`

## Pattern: rendering multiple scenes

```tsx
const SCENES = [
  { start: 0,   duration: 90  },  // scene 1: frames 0–89
  { start: 90,  duration: 60  },  // scene 2: frames 90–149
  { start: 150, duration: 120 },  // scene 3: frames 150–269
];

export const EventReel: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: '#000' }}>
    {SCENES.map((scene, i) => (
      <Sequence key={i} from={scene.start} durationInFrames={scene.duration}>
        <SceneFrame {...scene} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
```

## Computing cumulative start frames

```ts
const starts = scenes.reduce<number[]>((acc, scene, i) => {
  acc.push(i === 0 ? 0 : acc[i - 1] + scenes[i - 1].durationFrames);
  return acc;
}, []);
```

## Common error: overlapping sequences
Sequences do NOT automatically stack in time. You must manually compute the `from` offset by summing prior durations.
