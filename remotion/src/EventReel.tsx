import React from 'react';
import { AbsoluteFill, Sequence, Img, interpolate, spring, useCurrentFrame, useVideoConfig, staticFile } from 'remotion';

const scenes = [
  { 
    startFrame: 0, 
    durationFrames: 150, 
    imageFilename: 'AHD_6008.jpg', 
    animation: 'ken_burns', 
    transitionIn: 'fade', 
    caption: null 
  },
  { 
    startFrame: 150, 
    durationFrames: 150, 
    imageFilename: 'AHD_6020.jpg', 
    animation: 'zoom_in', 
    transitionIn: 'dissolve', 
    caption: 'two hearts become one' 
  },
  { 
    startFrame: 300, 
    durationFrames: 150, 
    imageFilename: 'AHD_6024.jpg', 
    animation: 'static', 
    transitionIn: 'fade', 
    caption: null 
  },
  { 
    startFrame: 450, 
    durationFrames: 150, 
    imageFilename: 'AHD_6008.jpg', 
    animation: 'zoom_out', 
    transitionIn: 'dissolve', 
    caption: null 
  },
  { 
    startFrame: 600, 
    durationFrames: 150, 
    imageFilename: 'AHD_6020.jpg', 
    animation: 'ken_burns', 
    transitionIn: 'fade', 
    caption: 'love is in the air' 
  },
  { 
    startFrame: 750, 
    durationFrames: 150, 
    imageFilename: 'AHD_6024.jpg', 
    animation: 'static', 
    transitionIn: 'dissolve', 
    caption: null 
  },
  { 
    startFrame: 900, 
    durationFrames: 150, 
    imageFilename: 'AHD_6008.jpg', 
    animation: 'zoom_in', 
    transitionIn: 'fade', 
    caption: null 
  },
  { 
    startFrame: 1050, 
    durationFrames: 150, 
    imageFilename: 'AHD_6020.jpg', 
    animation: 'ken_burns', 
    transitionIn: 'dissolve', 
    caption: null 
  },
];

const openingText = 'love story';
const closingText = 'happily ever after';

const calculateStartFrames = (scenes: any[]) => {
  const startFrames = scenes.reduce<number[]>((acc, scene, i) => {
    acc.push(i === 0 ? 0 : acc[i - 1] + scenes[i - 1].durationFrames);
    return acc;
  }, []);
  return startFrames;
};

const startFrames = calculateStartFrames(scenes);

export const EventReel: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: '#000' }}>
      {openingText && (
        <AbsoluteFill
          style={{
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: 64,
            fontFamily: 'sans-serif',
            color: 'white',
            textShadow: '0 2px 8px rgba(0,0,0,0.8)',
          }}
        >
          <Sequence from={0} durationInFrames={30}>
            <div
              style={{
                fontSize: 64,
                fontFamily: 'sans-serif',
                opacity: interpolate(useCurrentFrame(), [0, 15], [0, 1], { extrapolateRight: 'clamp' }),
              }}
            >
              {openingText}
            </div>
          </Sequence>
        </AbsoluteFill>
      )}
      {scenes.map((scene, i) => (
        <Sequence key={i} from={startFrames[i]} durationInFrames={scene.durationFrames}>
          <Scene
            imageFilename={scene.imageFilename}
            animation={scene.animation}
            transitionIn={scene.transitionIn}
            caption={scene.caption}
          />
        </Sequence>
      ))}
      {closingText && (
        <AbsoluteFill
          style={{
            justifyContent: 'center',
            alignItems: 'center',
            fontSize: 64,
            fontFamily: 'sans-serif',
            color: 'white',
            textShadow: '0 2px 8px rgba(0,0,0,0.8)',
          }}
        >
          <Sequence from={startFrames[startFrames.length - 1] + scenes[scenes.length - 1].durationFrames - 30} durationInFrames={30}>
            <div
              style={{
                fontSize: 64,
                fontFamily: 'sans-serif',
                opacity: interpolate(useCurrentFrame(), [0, 15], [0, 1], { extrapolateRight: 'clamp' }),
              }}
            >
              {closingText}
            </div>
          </Sequence>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

const Scene: React.FC<{
  imageFilename: string;
  animation: string;
  transitionIn: string;
  caption: string | null;
}> = ({ imageFilename, animation, transitionIn, caption }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  let style: any = {};
  let opacity: any = {};

  if (transitionIn === 'fade') {
    opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });
  } else if (transitionIn === 'dissolve') {
    opacity = interpolate(frame, [0, 15], [0.5, 1], { extrapolateRight: 'clamp' });
  }

  if (animation === 'ken_burns') {
    const scale = interpolate(frame, [0, 150], [1.0, 1.08], { extrapolateRight: 'clamp' });
    style = { transform: `scale(${scale})`, transformOrigin: 'center center' };
  } else if (animation === 'zoom_in') {
    const scale = interpolate(frame, [0, 150], [1.2, 1.0], { extrapolateRight: 'clamp' });
    style = { transform: `scale(${scale})`, transformOrigin: 'center center' };
  } else if (animation === 'zoom_out') {
    const scale = interpolate(frame, [0, 150], [1.0, 1.2], { extrapolateRight: 'clamp' });
    style = { transform: `scale(${scale})`, transformOrigin: 'center center' };
  } else if (animation === 'static') {
    style = {};
  }

  return (
    <AbsoluteFill style={{ ...style, opacity: opacity }}>
      <Img src={staticFile(imageFilename)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
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

export const VideoConfig = {
  duration: 1350,
  fps: 30,
  width: 1920,
  height: 1080,
};