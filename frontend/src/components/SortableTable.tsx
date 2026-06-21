import { useEffect, useMemo, useState } from "react";
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
  /** When set, paginate the sorted rows (e.g. 20 for long worklists). */
  pageSize?: number;
  onRowClick?: (row: T) => void;
  rowId?: (row: T) => string;
  selectedId?: string | null;
}

export function SortableTable<T>({
  columns,
  rows,
  initialSort,
  initialDir = "desc",
  pageSize,
  onRowClick,
  rowId,
  selectedId,
}: Props<T>) {
  const [sortKey, setSortKey] = useState<string | undefined>(initialSort);
  const [dir, setDir] = useState<"asc" | "desc">(initialDir);
  const [page, setPage] = useState(1);

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

  const totalPages = pageSize ? Math.max(1, Math.ceil(sorted.length / pageSize)) : 1;
  const safePage = Math.min(page, totalPages);

  useEffect(() => {
    setPage(1);
  }, [rows, sortKey, dir, pageSize]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  const visible = pageSize
    ? sorted.slice((safePage - 1) * pageSize, safePage * pageSize)
    : sorted;

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

  const from = sorted.length === 0 ? 0 : (safePage - 1) * (pageSize ?? sorted.length) + 1;
  const to = pageSize ? Math.min(safePage * pageSize, sorted.length) : sorted.length;

  return (
    <div>
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
            {visible.map((row, i) => {
              const id = rowId?.(row) ?? (row as { id?: string }).id;
              const selected = selectedId != null && id === selectedId;
              return (
              <tr
                key={id ?? i}
                className={selected ? "row-selected" : onRowClick ? "row-clickable" : undefined}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
              >
                {columns.map((c) => (
                  <td key={c.key} className={c.numeric ? "num" : undefined}>
                    {c.render(row)}
                  </td>
                ))}
              </tr>
            );
            })}
          </tbody>
        </table>
      </div>
      {pageSize && sorted.length > pageSize && (
        <div className="table-pagination">
          <span className="muted">
            Showing {from}–{to} of {sorted.length}
          </span>
          <div className="pagination-controls">
            <button
              type="button"
              className="graph-tool-btn"
              disabled={safePage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </button>
            <span className="pagination-page">
              Page {safePage} of {totalPages}
            </span>
            <button
              type="button"
              className="graph-tool-btn"
              disabled={safePage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
