import React, { useState } from 'react';
import { RotateCcw, Play, Pause, ChevronLeft, ChevronRight, FastForward, Cpu, Terminal, Layers } from 'lucide-react';
import { ReplayFrame } from '../types';

interface ReplayViewerProps {
  replayFrames: ReplayFrame[];
}

export const ReplayViewer: React.FC<ReplayViewerProps> = ({ replayFrames }) => {
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  if (!replayFrames || replayFrames.length === 0) {
    return (
      <div className="text-center py-20 bg-slate-900 border border-slate-800 rounded-xl">
        <p className="text-slate-400">No replay frames recorded for this investigation.</p>
      </div>
    );
  }

  const frame = replayFrames[currentFrameIndex] || replayFrames[0];

  React.useEffect(() => {
    let timer: any;
    if (isPlaying) {
      timer = setInterval(() => {
        setCurrentFrameIndex((prev) => {
          if (prev >= replayFrames.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);
    }
    return () => clearInterval(timer);
  }, [isPlaying, replayFrames.length]);

  return (
    <div className="space-y-6">
      {/* Playback Controls Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <RotateCcw className="h-5 w-5 text-brand-400" />
              <span>Step-by-Step Investigation Replay</span>
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Reconstruct the exact cognitive sequence, tool invocations, and belief updates at each step.
            </p>
          </div>

          {/* Player controls */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentFrameIndex(0)}
              className="p-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300"
              title="First step"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
            <button
              onClick={() => setCurrentFrameIndex((prev) => Math.max(prev - 1, 0))}
              disabled={currentFrameIndex === 0}
              className="p-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="px-3 py-1.5 rounded-md bg-brand-600 hover:bg-brand-500 text-white font-medium text-xs flex items-center space-x-1.5"
            >
              {isPlaying ? <Pause className="h-4 w-4 fill-current" /> : <Play className="h-4 w-4 fill-current" />}
              <span>{isPlaying ? 'Pause' : 'Play Replay'}</span>
            </button>
            <button
              onClick={() => setCurrentFrameIndex((prev) => Math.min(prev + 1, replayFrames.length - 1))}
              disabled={currentFrameIndex === replayFrames.length - 1}
              className="p-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-50"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Scrubber Slider */}
        <div className="mt-5 space-y-1.5">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400">
            <span>Frame {currentFrameIndex + 1} of {replayFrames.length}</span>
            <span className="text-brand-400 font-semibold">{frame.phase}</span>
            <span>Confidence: {frame.confidence_at_step.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min={0}
            max={replayFrames.length - 1}
            value={currentFrameIndex}
            onChange={(e) => setCurrentFrameIndex(Number(e.target.value))}
            className="w-full accent-brand-500 bg-slate-800 rounded-lg cursor-pointer h-2"
          />
        </div>
      </div>

      {/* Frame State Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Agent Cognitive State at this frame */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5 mb-2">
              <Cpu className="h-3.5 w-3.5 text-brand-400" />
              <span>Agent Thought at Step {frame.step_number}</span>
            </h3>
            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs text-slate-200 font-mono leading-relaxed">
              {frame.current_thought}
            </div>
          </div>

          {frame.executed_query && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5 mb-2">
                <Terminal className="h-3.5 w-3.5 text-indigo-400" />
                <span>Chosen Action</span>
              </h3>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs text-indigo-300 font-mono">
                {frame.executed_query}
              </div>
            </div>
          )}

          {frame.latest_evidence && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5 mb-2">
                <Layers className="h-3.5 w-3.5 text-amber-400" />
                <span>Evidence Collected in this Frame</span>
              </h3>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs text-amber-300 font-mono">
                {frame.latest_evidence?.observation?.summary}
              </div>
            </div>
          )}
        </div>

        {/* Right: Hypotheses Belief Snapshot */}
        <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold mb-3">
            Hypothesis Probabilities at this Snapshot
          </h3>

          <div className="space-y-3">
            {frame.active_hypotheses?.map((h: any) => (
              <div key={h.id} className="bg-slate-950 p-3 rounded-lg border border-slate-800/80">
                <div className="flex items-center justify-between text-xs font-mono mb-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-white">{h.id}</span>
                    <span className="text-slate-500 uppercase text-[10px]">{h.category}</span>
                  </div>
                  <span className="font-bold text-emerald-400">{(h.current_score * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 transition-all duration-300"
                    style={{ width: `${Math.min(Math.max(h.current_score * 100, 2), 100)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
