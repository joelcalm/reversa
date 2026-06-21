import { useEffect, useState, type ReactNode } from "react";

interface Chip {
  id: string;
  label: string;
}

interface Props {
  chips: Chip[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  graph: ReactNode;
  panel: ReactNode;
  table?: ReactNode;
  showTable?: boolean;
}

export default function BriefingBody({ chips, selectedId, onSelect, graph, panel, table, showTable }: Props) {
  return (
    <>
      {chips.length > 0 && (
        <div className="hub-chips">
          {chips.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`chip ${selectedId === c.id ? "active" : ""}`}
              onClick={() => onSelect(c.id)}
            >
              {c.label}
            </button>
          ))}
        </div>
      )}
      <div className="briefing-split">
        <div className="briefing-graph-col">{graph}</div>
        <div className="briefing-panel-col">{panel}</div>
      </div>
      {showTable && table && <div className="briefing-table-wrap">{table}</div>}
    </>
  );
}

export function useDefaultSelection<T extends { id: string }>(
  items: T[] | undefined,
  initialId?: string | null,
): [string | null, (id: string) => void] {
  const [selectedId, setSelectedId] = useState<string | null>(initialId ?? null);
  useEffect(() => {
    if (!items?.length) return;
    if (!selectedId || !items.some((i) => i.id === selectedId)) {
      setSelectedId(items[0].id);
    }
  }, [items, selectedId]);
  return [selectedId, setSelectedId];
}
