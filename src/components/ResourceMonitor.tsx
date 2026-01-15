import { useEffect, useState } from "react";
import { Activity, MemoryStick } from "lucide-react";
import { api } from "@/lib/api";
import type { ResourceUsage } from "@/lib/types";

export function ResourceMonitor() {
  const [resources, setResources] = useState<ResourceUsage | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getResourceUsage();
        setResources(data);
      } catch (error) {
        setResources({
          cpuPercent: 0,
          memoryMb: 0,
        });
      }
    };

    // Load immediately
    load();

    // Poll every 2 seconds
    const interval = setInterval(load, 2000);

    return () => clearInterval(interval);
  }, []);

  if (!resources) {
    return (
      <div className="flex items-center gap-3 animate-pulse">
        <div className="p-2 bg-muted/20 rounded-xl w-10 h-10" />
        <div className="flex-1">
          <div className="h-3 bg-muted/20 rounded w-24 mb-2" />
          <div className="h-4 bg-muted/20 rounded w-16" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* CPU Usage */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-500/20 rounded-xl text-blue-400">
          <Activity className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-widest mb-0.5">
            CPU Usage
          </p>
          <p className="text-lg text-foreground font-bold leading-none">
            {resources.cpuPercent.toFixed(1)}
            <span className="text-sm font-normal text-muted-foreground ml-1">
              %
            </span>
          </p>
        </div>
      </div>

      {/* Memory Usage */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple-500/20 rounded-xl text-purple-400">
          <MemoryStick className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <p className="text-[10px] text-muted-foreground font-semibold uppercase tracking-widest mb-0.5">
            Memory Usage
          </p>
          <p className="text-lg text-foreground font-bold leading-none">
            {resources.memoryMb.toFixed(1)}
            <span className="text-sm font-normal text-muted-foreground ml-1">
              MB
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
