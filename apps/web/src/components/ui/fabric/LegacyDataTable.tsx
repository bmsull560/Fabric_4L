/**
 * LegacyDataTable — String-column / ReactNode-row table API.
 *
 * Use the typed `DataTable` (`@/components/ui/fabric/DataTable`) for new code.
 * This component preserves the legacy API used by existing callers.
 * Migrated from WfPrimitives shim.
 */
import type { ReactNode } from "react";
import { DataTable } from "./DataTable";
import type { DataTableColumn } from "./DataTable";

export interface LegacyDataTableProps {
  columns: string[];
  rows: ReactNode[][];
  emptyMessage?: string;
  onRowClick?: (index: number, rowId?: string) => void;
  selectedRowIndex?: number;
  rowIds?: string[];
}

export function LegacyDataTable({
  columns,
  rows,
  emptyMessage = "No data found",
  onRowClick,
  selectedRowIndex,
  rowIds,
}: LegacyDataTableProps) {
  const fabricColumns: DataTableColumn<ReactNode[]>[] = columns.map((col, index) => ({
    key: String(index),
    header: col,
    render: (row) => row[index],
  }));

  return (
    <DataTable
      data={rows}
      columns={fabricColumns}
      keyExtractor={(item) => {
        const index = rows.indexOf(item);
        return rowIds?.[index] ?? String(index);
      }}
      emptyMessage={emptyMessage}
      onRowClick={
        onRowClick
          ? (item) => {
              const index = rows.indexOf(item);
              onRowClick(index, rowIds?.[index]);
            }
          : undefined
      }
      selectedKey={selectedRowIndex !== undefined ? (rowIds?.[selectedRowIndex] ?? String(selectedRowIndex)) : undefined}
    />
  );
}
