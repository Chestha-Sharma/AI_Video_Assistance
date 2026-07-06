import React from 'react'

const ResultsSkeleton = () => {
  return (
    <div className="p-6 space-y-4 animate-pulse">
      <div className="h-6 w-2/3 bg-base-300 rounded" />
      <div className="flex gap-1 items-end h-10">
        {Array(12)
          .fill(null)
          .map((_, i) => (
            <div
              key={i}
              className="wave-bar w-1.5 bg-primary/60 rounded-full"
              style={{ height: `${20 + ((i * 37) % 60)}%`, animationDelay: `${i * 0.07}s` }}
            />
          ))}
      </div>
      <div className="h-4 w-full bg-base-300 rounded" />
      <div className="h-4 w-5/6 bg-base-300 rounded" />
      <div className="h-4 w-2/3 bg-base-300 rounded" />
    </div>
  )
}

export default ResultsSkeleton
