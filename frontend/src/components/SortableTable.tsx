import { useMemo, useState } from "react";
import type { ReactNode } from "react";

export interface Column<T> {
  key: string;
  label: string;
  numeric?: boolean;
  render: (row: T) => ReactNode;
  sortValue?: (row: T) => string | number;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  initialSort?: string;
  initialDir?: "asc" | "desc";
}

export function SortableTable<T>({ columns, rows, initialSort, initialDir = "desc" }: Props<T>) {
  const [sortKey, setSortKey] = useState<string | undefined>(initialSort);
  const [dir, setDir] = useState<"asc" | "desc">(initialDir);

  const sorted = useMemo(() => {
    if (!sortKey) return rows;
    const col = columns.find((c) => c.key === sortKey);
    if (!col?.sortValue) return rows;
    const factor = dir === "asc" ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = col.sortValue!(a);
      const bv = col.sortValue!(b);
      if (av < bv) return -1 * factor;
      if (av > bv) return 1 * factor;
      return 0;
    });
  }, [rows, columns, sortKey, dir]);

  const onSort = (key: string) => {
    const col = columns.find((c) => c.key === key);
    if (!col?.sortValue) return;
    if (sortKey === key) {
      setDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setDir("desc");
    }
  };

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                onClick={() => onSort(c.key)}
                style={{ cursor: c.sortValue ? "pointer" : "default" }}
              >
                {c.label}
                {sortKey === c.key ? (dir === "asc" ? " ▲" : " ▼") : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c.key} className={c.numeric ? "num" : undefined}>
                  {c.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
