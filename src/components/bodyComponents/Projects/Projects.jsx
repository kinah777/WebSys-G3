import { useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Typography, CircularProgress, Chip } from "@mui/material";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const statusColor = (status) => {
  switch (status) {
    case "Ongoing": return "primary";
    case "Completed": return "success";
    case "Planning": return "info";
    case "On Hold": return "warning";
    default: return "default";
  }
};

const columns = [
  { field: "project_id", headerName: "ID", width: 110 },
  { field: "project_name", headerName: "Project Name", flex: 1 },
  { field: "location", headerName: "Location", width: 150 },
  {
    field: "status", headerName: "Status", width: 130,
    renderCell: (params) => (
      <Chip label={params.value} color={statusColor(params.value)} size="small" />
    ),
  },
  { field: "completion_percentage", headerName: "% Done", width: 90, type: "number" },
  { field: "start_date", headerName: "Start Date", width: 120 },
  { field: "end_date", headerName: "End Date", width: 120 },
];

export default function Projects() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE}/projects`)
      .then((r) => r.json())
      .then((data) => setRows(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <Box sx={{ p: 4, height: "85vh" }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 2, color: "text.secondary" }}>
        Construction Projects
      </Typography>
      {loading ? (
        <CircularProgress sx={{ mt: 4 }} color="primary" />
      ) : (
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(row) => row.project_id}
          pageSizeOptions={[25, 50, 100]}
          initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
        />
      )}
    </Box>
  );
}
