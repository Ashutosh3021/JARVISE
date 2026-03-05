import React from 'react';

interface WaveformProps {
  isAnimating: boolean;
}

const Waveform: React.FC<WaveformProps> = ({ isAnimating }) => {
  if (!isAnimating) return null;
  
  return (
    <div className="flex items-end justify-center gap-1 h-6 px-2 py-1 bg-slate-700 rounded-2xl">
      {[...Array(7)].map((_, i) => (
        <div
          key={i}
          className="w-1 bg-teal-500 rounded-t"
          style={{
            height: '100%',
            animation: `waveform-bar 0.5s ease-in-out infinite`,
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
      <style>{`
        @keyframes waveform-bar {
          0%, 100% { transform: scaleY(0.2); }
          50% { transform: scaleY(1); }
        }
      `}</style>
    </div>
  );
};

export default Waveform;
