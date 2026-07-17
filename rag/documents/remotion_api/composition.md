# Remotion: Composition Registration

## registerRoot and RemotionRoot

Every Remotion project must call `registerRoot` in its entry file.

```tsx
// src/index.ts
import { registerRoot } from 'remotion';
import { RemotionRoot } from './Root';

registerRoot(RemotionRoot);
```

## Composition component

Use `<Composition>` inside the root to declare a renderable composition.

```tsx
import { Composition } from 'remotion';
import { MyVideo } from './MyVideo';

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MyVideo"           // must match the ID used in `npx remotion render`
      component={MyVideo}
      durationInFrames={300} // total frames = duration_seconds * fps
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
```

## Calculating durationInFrames from seconds

```ts
const FPS = 30;
const durationSeconds = 45;
const durationInFrames = Math.ceil(durationSeconds * FPS); // 1350
```

## Common error: ID mismatch
The `id` prop in `<Composition>` must exactly match the composition name passed to `npx remotion render <id>`.
