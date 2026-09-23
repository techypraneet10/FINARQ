import React from 'react';
import { LayoutBlockResponse } from '../../api/types';

export interface BoundingBoxOverlayProps {
  blocks: LayoutBlockResponse[];
  width: number;
  height: number;
  selectedBlockId?: string | null;
  onSelectBlock?: (block: LayoutBlockResponse) => void;
}

export const BoundingBoxOverlay: React.FC<BoundingBoxOverlayProps> = ({
  blocks,
  width,
  height,
  selectedBlockId,
  onSelectBlock,
}) => {
  if (!width || !height || width <= 0 || height <= 0) {
    return null;
  }

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="absolute inset-0 w-full h-full pointer-events-auto"
      style={{ mixBlendMode: 'plus-lighter' }}
    >
      {blocks.map((block) => {
        if (!block.bounding_box) return null;
        const { x0, y0, x1, y1 } = block.bounding_box;
        const boxWidth = Math.max(x1 - x0, 2);
        const boxHeight = Math.max(y1 - y0, 2);
        const isSelected = selectedBlockId === block.id;
        const isTable = block.block_type === 'table';

        return (
          <g key={block.id} className="cursor-pointer group" onClick={() => onSelectBlock && onSelectBlock(block)}>
            <rect
              x={x0}
              y={y0}
              width={boxWidth}
              height={boxHeight}
              fill={isSelected ? 'rgba(16, 185, 129, 0.25)' : isTable ? 'rgba(6, 182, 212, 0.12)' : 'rgba(51, 65, 85, 0.1)'}
              stroke={isSelected ? '#10b981' : isTable ? '#06b6d4' : '#475569'}
              strokeWidth={isSelected ? 2 : 1}
              strokeDasharray={isSelected ? undefined : '3 3'}
              rx={2}
              className="transition-all group-hover:fill-emerald-500/20 group-hover:stroke-emerald-400"
            />
            {isSelected && (
              <text
                x={x0}
                y={Math.max(y0 - 4, 12)}
                fill="#10b981"
                fontSize="10"
                fontFamily="JetBrains Mono, monospace"
                fontWeight="bold"
              >
                {block.block_type.toUpperCase()} [{x0.toFixed(0)}, {y0.toFixed(0)}]
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
};
