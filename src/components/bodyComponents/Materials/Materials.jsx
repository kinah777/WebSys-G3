import { useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Typography, CircularProgress } from "@mui/material";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const columns = [
  { field: "material_id", headerName: "ID", width: 110 },
  { field: "material_name", headerName: "Material Name", flex: 1 },
  { field: "category", headerName: "Category", width: 150 },
  { field: "unit", headerName: "Unit", width: 90 },
  { field: "unit_cost", headerName: "Unit Cost (₱)", width: 130, type: "number" },
  { field: "stock_quantity", headerName: "Stock Qty", width: 110, type: "number" },
  { field: "reorder_level", headerName: "Reorder Level", width: 130, type: "number" },
  { field: "supplier_id", headerName: "Supplier ID", width: 120 },
];

export default function Materials() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE}/materials`)
      .then((r) => r.json())
      .then((data) => setRows(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box sx={{ p: 4, height: "85vh" }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 2, color: "text.secondary" }}>
        Materials &amp; Supply Chain
      </Typography>
      {loading ? (
        <CircularProgress sx={{ mt: 4 }} color="primary" />
      ) : (
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(row) => row.material_id}
          pageSizeOptions={[25, 50, 100]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        />
      )}
    </Box>
  );
}
