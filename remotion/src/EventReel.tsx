import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  Img,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  staticFile,
} from 'remotion';

const SCENES = [
  {
    image: 'AHD_6008.jpg',
    durationFrames: 180,
    animation: 'ken_burns',
    caption: null,
  },
  {
    image: 'AHD_6020.jpg',
    durationFrames: 150,
    animation: 'ken_burns',
    caption: 'Their love shines bright',
  },
  {
    image: 'AHD_6024.jpg',
    durationFrames: 180,
    animation: 'ken_burns',
    caption: null,
  },
] as const;

const opening_text = 'A moment of forever';
const closing_text = 'Congratulations to the happy couple';

const SceneFrame: React.FC<{
  image: string;
  durationFrames: number;
  animation: 'ken_burns';
  caption: string | null;
}> = ({ image, durationFrames, animation, caption }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = interpolate(frame, [0, durationFrames], [1, 1.08], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill>
      <Img
        src={staticFile(image)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center',
          transform: `scale(${scale})`,
        }}
      />
      {caption && (
        <AbsoluteFill
          style={{
            justifyContent: 'flex-end',
            alignItems: 'center',
            paddingBottom: 60,
          }}
        >
          <div
            style={{
              color: 'white',
              fontSize: 42,
              fontFamily: 'sans-serif',
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
              opacity: interpolate(frame, [0, 20], [0, 1], {
                extrapolateRight: 'clamp',
              }),
            }}
          >
            {caption}
          </div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

const FadeInTransition: React.FC<{
  children: React.ReactNode;
  durationInFrames: number;
}> = ({ children, durationInFrames }) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      {children}
    </AbsoluteFill>
  );
};

const FadeOutTransition: React.FC<{
  children: React.ReactNode;
  durationOutFrames: number;
}> = ({ children, durationOutFrames }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const opacity = interpolate(
    frame,
    [durationInFrames - durationOutFrames, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      {children}
    </AbsoluteFill>
  );
};

export const EventReel: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {opening_text && (
        <Sequence from={0} durationInFrames={30}>
          <AbsoluteFill
            style={{
              justifyContent: 'center',
              alignItems: 'center',
              fontSize: 60,
              fontFamily: 'sans-serif',
              color: 'white',
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            {opening_text}
          </AbsoluteFill>
        </Sequence>
      )}
      {SCENES.map((scene, i) => (
        <Sequence
          key={i}
          from={i === 0 ? 0 : SCENES.slice(0, i).reduce((acc, s) => acc + s.durationFrames, 0)}
          durationInFrames={scene.durationFrames}
        >
          {i > 0 && (
            <FadeInTransition durationInFrames={15}>
              <SceneFrame {...scene} />
            </FadeInTransition>
          )}
          {i === 0 ? (
            <SceneFrame {...scene} />
          ) : (
            <FadeOutTransition durationOutFrames={15}>
              <SceneFrame {...scene} />
            </FadeOutTransition>
          )}
        </Sequence>
      ))}
      {closing_text && (
        <Sequence
          from={
            SCENES.reduce((acc, s) => acc + s.durationFrames, 0) - 30
          }
          durationInFrames={30}
        >
          <AbsoluteFill
            style={{
              justifyContent: 'center',
              alignItems: 'center',
              fontSize: 60,
              fontFamily: 'sans-serif',
              color: 'white',
              textShadow: '0 2px 8px rgba(0,0,0,0.8)',
            }}
          >
            {closing_text}
          </AbsoluteFill>
        </Sequence>
      )}
    </AbsoluteFill>
  );
};

export default EventReel;