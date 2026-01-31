'use client';

import React from 'react';

export type Stage = 'idle' | 'first_opinions' | 'review' | 'final_response' | 'complete';

interface StageIndicatorProps {
  currentStage: Stage;
  stageMessage?: string;
}

const stages = [
  { id: 'first_opinions', label: 'First Opinions', icon: '💭' },
  { id: 'review', label: 'Peer Review', icon: '⚖️' },
  { id: 'final_response', label: 'Final Response', icon: '📜' },
];

export default function StageIndicator({ currentStage, stageMessage }: StageIndicatorProps) {
  const getStageStatus = (stageId: string): 'pending' | 'active' | 'complete' => {
    const stageOrder = ['first_opinions', 'review', 'final_response', 'complete'];
    const currentIndex = stageOrder.indexOf(currentStage);
    const stageIndex = stageOrder.indexOf(stageId);

    if (currentStage === 'idle') return 'pending';
    if (stageIndex < currentIndex || currentStage === 'complete') return 'complete';
    if (stageIndex === currentIndex) return 'active';
    return 'pending';
  };

  if (currentStage === 'idle') return null;

  return (
    <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        {stages.map((stage, index) => {
          const status = getStageStatus(stage.id);

          return (
            <React.Fragment key={stage.id}>
              <div className="flex flex-col items-center">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-all ${
                    status === 'complete'
                      ? 'bg-green-500 dark:bg-green-600 text-white'
                      : status === 'active'
                      ? 'bg-blue-500 dark:bg-blue-600 text-white animate-pulse'
                      : 'bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {status === 'complete' ? '✓' : stage.icon}
                </div>
                <span
                  className={`mt-2 text-xs font-medium ${
                    status === 'active' ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'
                  }`}
                >
                  {stage.label}
                </span>
              </div>

              {index < stages.length - 1 && (
                <div className="flex-1 h-1 mx-2 bg-gray-300 dark:bg-gray-600 relative">
                  <div
                    className={`absolute top-0 left-0 h-full transition-all duration-500 ${
                      getStageStatus(stages[index + 1].id) !== 'pending'
                        ? 'bg-green-500 dark:bg-green-600 w-full'
                        : 'bg-gray-300 dark:bg-gray-600 w-0'
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {stageMessage && (
        <div className="text-sm text-gray-600 dark:text-gray-300 text-center mt-2 animate-pulse">
          {stageMessage}
        </div>
      )}
    </div>
  );
}
