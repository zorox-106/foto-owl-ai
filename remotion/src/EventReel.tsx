import React from 'react';
import { AbsoluteFill, Sequence, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from 'remotion';

const opening_text = 'A Moment in Time';
const closing_text = 'Forever Entwined';

const SCENES = [
  {
    image: 'AHD_6008.jpg',
    startFrame: 0,
    durationFrames: 180,
    animation: 'ken_burns',
    caption: null,
  },
  {
    image: 'AHD_6020.jpg',
    startFrame: 180,
    durationFrames: 150,
    animation: 'zoom_in',
    caption: 'Their love story unfolds',
  },
  {
    image: 'AHD_6024.jpg',
    startFrame: 330,
    durationFrames: 180,
    animation: 'static',
    caption: null,
  },
];

const SceneFrame = ({ image, durationFrames, animation, caption }: { image: string; durationFrames: number; animation: string; caption: string | null }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
  const scale = animation === 'ken_burns' ? interpolate(frame, [0, durationFrames], [1, 1.08], { extrapolateRight: 'clamp' }) : 1;
  const style = { transform: `scale(${scale})`, transformOrigin: 'center center' };

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <Img
        src={staticFile(image)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center',
          opacity,
          ...style,
        }}
      />
      {caption && (
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
      )}
    </AbsoluteFill>
  );
};

const OpeningText = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div
        style={{
          color: 'white',
          fontSize: 64,
          fontFamily: 'sans-serif',
          textShadow: '0 2px 8px rgba(0,0,0,0.8)',
          opacity,
        }}
      >
        {opening_text}
      </div>
    </AbsoluteFill>
  );
};

const ClosingText = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const opacity = interpolate(frame, [durationInFrames - 30, durationInFrames], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
      <div
        style={{
          color: 'white',
          fontSize: 64,
          fontFamily: 'sans-serif',
          textShadow: '0 2px 8px rgba(0,0,0,0.8)',
          opacity,
        }}
      >
        {closing_text}
      </div>
    </AbsoluteFill>
  );
};

export const EventReel: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: '#000' }}>
    <Sequence from={0} durationInFrames={30}>
      <OpeningText />
    </Sequence>
    {SCENES.map((scene, i) => (
      <Sequence key={i} from={scene.startFrame} durationInFrames={scene.durationFrames}>
        <SceneFrame {...scene} />
      </Sequence>
    ))}
    <Sequence from={1350 - 30} durationInFrames={30}>
      <ClosingText />
    </Sequence>
  </AbsoluteFill>
);

export default EventReel;