import { useState, useEffect } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { Box, Typography, CircularProgress, Chip } from "@mui/material";
import ReactApexChart from "react-apexcharts";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const statusColor = (status) => {
  switch (status) {
    case "Active": return "success";
    case "Closed": return "error";
    case "Draft": return "warning";
    default: return "default";
  }
};

const columns = [
  { field: "budget_id", headerName: "ID", width: 110 },
  { field: "project_id", headerName: "Project ID", width: 120 },
  { field: "total_budget", headerName: "Total Budget (₱)", width: 160, type: "number" },
  { field: "labor_cost", headerName: "Labor (₱)", width: 130, type: "number" },
  { field: "material_cost", headerName: "Materials (₱)", width: 140, type: "number" },
  { field: "equipment_cost", headerName: "Equipment (₱)", width: 140, type: "number" },
  { field: "actual_spent", headerName: "Spent (₱)", width: 130, type: "number" },
  { field: "remaining_budget", headerName: "Remaining (₱)", width: 140, type: "number" },
];

export default function Financials() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${BASE}/budgets`)
      .then((r) => r.json())
      .then((data) => setRows(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const totalBudget = rows.reduce((s, r) => s + (r.total_budget || 0), 0);
  const totalSpent = rows.reduce((s, r) => s + (r.actual_spent || 0), 0);
  const totalLabor = rows.reduce((s, r) => s + (r.labor_cost || 0), 0);
  const totalMaterial = rows.reduce((s, r) => s + (r.material_cost || 0), 0);
  const totalEquipment = rows.reduce((s, r) => s + (r.equipment_cost || 0), 0);

  const chartOptions = {
    chart: { type: "bar", toolbar: { show: false } },
    xaxis: { categories: ["Labor", "Materials", "Equipment", "Total Spent"] },
    colors: ["#D84A05"],
    dataLabels: { enabled: false },
    yaxis: { labels: { formatter: (v) => `₱${(v / 1_000_000).toFixed(1)}M` } },
  };
  const chartSeries = [
    { name: "Cost (₱)", data: [totalLabor, totalMaterial, totalEquipment, totalSpent] },
  ];

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h5" fontWeight={700} sx={{ mb: 2, color: "text.secondary" }}>
        Financials &amp; Forecasting
      </Typography>
      {!loading && (
        <Box sx={{ mb: 3 }}>
          <ReactApexChart type="bar" options={chartOptions} series={chartSeries} height={220} />
        </Box>
      )}
      <Box sx={{ height: "55vh" }}>
        {loading ? (
          <CircularProgress sx={{ mt: 4 }} color="primary" />
        ) : (
          <DataGrid
            rows={rows}
            columns={columns}
            getRowId={(row) => row.budget_id}
            pageSizeOptions={[25, 50, 100]}
            initialState={{ pagination: { paginationModel: { pageSize: 25 } } }}
          />
        )}
      </Box>
    </Box>
  );
}
