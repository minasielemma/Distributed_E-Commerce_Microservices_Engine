import React, { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

export const CountdownTimer = ({ endTime, className = '' }) => {
  const [timeLeft, setTimeLeft] = useState(null);

  useEffect(() => {
    if (!endTime) return;

    const targetTime = new Date(endTime).getTime();

    const updateTimer = () => {
      const now = Date.now();
      const diff = targetTime - now;

      if (diff <= 0) {
        setTimeLeft(null);
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
      const minutes = Math.floor((diff / (1000 * 60)) % 60);
      const seconds = Math.floor((diff / 1000) % 60);

      setTimeLeft({ days, hours, minutes, seconds });
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);
    return () => clearInterval(interval);
  }, [endTime]);

  if (!timeLeft) return null;

  const { days, hours, minutes, seconds } = timeLeft;

  const formatSegment = (val) => String(val).padStart(2, '0');

  let formatted = '';
  if (days > 0) {
    formatted = `${days}d ${hours}h ${minutes}m ${seconds}s`;
  } else {
    formatted = `${formatSegment(hours)}:${formatSegment(minutes)}:${formatSegment(seconds)}`;
  }

  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-red-50 border border-red-200 text-[#CC0C39] text-xs font-semibold font-mono ${className}`}>
      <Clock className="w-3.5 h-3.5 shrink-0 animate-pulse text-[#CC0C39]" />
      <span>Ends in {formatted}</span>
    </div>
  );
};
