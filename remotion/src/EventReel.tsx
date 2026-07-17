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
    start: 0,
    duration: 180,
    animation: 'ken_burns',
    caption: '',
  },
  {
    image: 'AHD_6020.jpg',
    start: 180,
    duration: 150,
    animation: 'zoom_in',
    caption: 'Their love shines bright',
  },
  {
    image: 'AHD_6024.jpg',
    start: 330,
    duration: 180,
    animation: 'static',
    caption: '',
  },
] as const;

const opening_text = 'A moment to remember';
const closing_text = 'Forever begins';

const SceneFrame: React.FC<{
  image: string;
  durationFrames: number;
  animation: 'ken_burns' | 'zoom_in' | 'static';
  caption: string;
  style?: React.CSSProperties;
}> = ({ image, durationFrames, animation, caption, style = {} }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const src = staticFile(image);

  let scale = 1.0;
  let additionalStyle: React.CSSProperties = {};

  switch (animation) {
    case 'ken_burns':
      scale = interpolate(frame, [0, durationFrames], [1.0, 1.08], {
        extrapolateRight: 'clamp',
      });
      additionalStyle = { transform: `scale(${scale})`, transformOrigin: 'center center' };
      break;
    case 'zoom_in':
      const opacity = interpolate(frame, [0, 20], [0, 1], {
        extrapolateRight: 'clamp',
      });
      const translateX = interpolate(frame, [0, 20], [10, 0], {
        extrapolateRight: 'clamp',
      });
      additionalStyle = {
        opacity,
        transform: `translateX(${translateX}%)`,
      };
      break;
    case 'static':
      break;
  }

  return (
    <AbsoluteFill>
      <Img
        src={src}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center',
          ...additionalStyle,
          ...style,
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

const OpeningText: React.FC = () => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        paddingTop: 180,
      }}
    >
      <div
        style={{
          color: 'white',
          fontSize: 72,
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

const ClosingText: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const opacity = interpolate(
    frame,
    [durationInFrames - 60, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        paddingBottom: 180,
      }}
    >
      <div
        style={{
          color: 'white',
          fontSize: 72,
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

export const EventReel: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      <Sequence from={0} durationInFrames={30}>
        <OpeningText />
      </Sequence>
      {SCENES.map((scene, i) => (
        <Sequence
          key={i}
          from={scene.start}
          durationInFrames={scene.duration}
          layout="absolute-fill"
        >
          {i === 0 ? (
            <></>
          ) : (
            <SceneFrame
              image={SCENES[i - 1].image}
              durationFrames={30}
              animation="static"
              caption=""
              style={{ opacity: interpolate(useCurrentFrame(), [0, 30], [1, 0]) }}
            />
          )}
          <SceneFrame
            image={scene.image}
            durationFrames={scene.duration}
            animation={scene.animation}
            caption={scene.caption}
          />
        </Sequence>
      ))}
      <Sequence from={1350 - 30} durationInFrames={30}>
        <ClosingText />
      </Sequence>
    </AbsoluteFill>
  );
};

export default EventReel;