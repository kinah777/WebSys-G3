import { useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Typography, CircularProgress, Chip } from "@mui/material";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const statusColor = (status) => {
  switch (status) {
    case "Available": return "success";
    case "In Use": return "primary";
    case "Under Maintenance": return "warning";
    case "Retired": return "error";
    default: return "default";
  }
};

const columns = [
  { field: "equipment_id", headerName: "ID", width: 110 },
  { field: "equipment_name", headerName: "Equipment Name", flex: 1 },
  { field: "equipment_type", headerName: "Type", width: 150 },
  {
    field: "status", headerName: "Status", width: 150,
    renderCell: (params) => (
      <Chip label={params.value} color={statusColor(params.value)} size="small" />
    ),
  },
  { field: "location", headerName: "Location", width: 150 },
  { field: "purchase_date", headerName: "Purchase Date", width: 130 },
  { field: "daily_rental_cost", headerName: "Daily Rate (₱)", width: 130, type: "number" },
];

export default function Equipment() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE}/equipment`)
      .then((r) => r.json())
      .then((data) => setRows(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box sx={{ p: 4, height: "85vh" }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 2, color: "text.secondary" }}>
        Equipment &amp; Fleet
      </Typography>
      {loading ? (
        <CircularProgress sx={{ mt: 4 }} color="primary" />
      ) : (
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(row) => row.equipment_id}
          pageSizeOptions={[25, 50, 100]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        />
      )}
    </Box>
  );
}
