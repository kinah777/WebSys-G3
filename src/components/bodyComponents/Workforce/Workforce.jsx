import { useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Typography, CircularProgress, Chip } from "@mui/material";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const statusColor = (status) => {
  switch (status) {
    case "Active": return "success";
    case "Inactive": return "error";
    case "On Leave": return "warning";
    default: return "default";
  }
};

const columns = [
  { field: "employee_id", headerName: "ID", width: 110 },
  { field: "first_name", headerName: "First Name", width: 130 },
  { field: "last_name", headerName: "Last Name", width: 130 },
  { field: "role", headerName: "Role", flex: 1 },
  { field: "department", headerName: "Department", width: 160 },
  {
    field: "employment_status", headerName: "Status", width: 130,
    renderCell: (params) => (
      <Chip label={params.value} color={statusColor(params.value)} size="small" />
    ),
  },
  { field: "daily_rate", headerName: "Daily Rate (₱)", width: 130, type: "number" },
];

export default function Workforce() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE}/employees`)
      .then((r) => r.json())
      .then((data) => setRows(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box sx={{ p: 4, height: "85vh" }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 2, color: "text.secondary" }}>
        Workforce &amp; Labor
      </Typography>
      {loading ? (
        <CircularProgress sx={{ mt: 4 }} color="primary" />
      ) : (
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(row) => row.employee_id}
          pageSizeOptions={[25, 50, 100]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        />
      )}
    </Box>
  );
}
