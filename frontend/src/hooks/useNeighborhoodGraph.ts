import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { GraphData } from "../types";

interface Options {
  normId: string | null;
  relationType?: string;
  direction?: "all" | "incoming" | "outgoing";
  limit?: number;
  nodeEnricher?: (data: GraphData) => GraphData;
}

export function useNeighborhoodGraph({
  normId,
  relationType,
  direction = "all",
  limit = 120,
  nodeEnricher,
}: Options) {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!normId) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .neighborhood(normId, { relationType, direction, limit })
      .then((g) => {
        if (cancelled) return;
        const enriched = nodeEnricher ? nodeEnricher(g) : g;
        // Mark hub
        const nodes = enriched.nodes.map((n) => ({
          ...n,
          data: {
            ...n.data,
            is_hub: n.data.id === normId ? true : n.data.is_hub,
          },
        }));
        setData({
          ...enriched,
          nodes,
          meta: { ...enriched.meta, focus_id: normId },
        });
      })
      .catch((e: Error) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [normId, relationType, direction, limit]);

  return { data, loading, error };
}
