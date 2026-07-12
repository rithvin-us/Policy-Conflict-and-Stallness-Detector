"use client";

import { useState, useEffect } from "react";

export function Clock() {
  const [time, setTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      setTime(new Date().toLocaleTimeString(undefined, { 
        hour: 'numeric', 
        minute: '2-digit', 
        second: '2-digit',
        hour12: true 
      }));
    };
    
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Hydration safety: render nothing or a generic placeholder until mounted
  if (!time) return <span className="mono text-black font-semibold min-w-[80px] text-right">--:--:--</span>;

  return (
    <span className="mono text-black font-bold tracking-wide">
      {time}
    </span>
  );
}
