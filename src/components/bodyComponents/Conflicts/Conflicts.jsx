import { useState, useEffect } from "react";
import {
  Box, Typography, CircularProgress, Chip,
  Card, CardContent, Divider, Button,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const typeColor = (type) => {
  switch (type) {
    case "equipment": return "warning";
    case "vehicle": return "info";
    case "employee": return "error";
    default: return "default";
  }
};

export default function Conflicts() {
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchConflicts = () => {
    setLoading(true);
    fetch(`${BASE}/conflicts`)
      .then((r) => r.json())
      .then((data) => setConflicts(Array.isArray(data) ? data : []))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchConflicts(); }, []);

  return (
    <Box sx={{ p: 4 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <WarningAmberIcon color="warning" sx={{ fontSize: 32 }} />
        <Typography variant="h5" fontWeight={700} sx={{ color: "text.secondary" }}>
          Conflict Resolution Center
        </Typography>
        <Button variant="outlined" color="primary" size="small" onClick={fetchConflicts} sx={{ ml: "auto" }}>
          Refresh
        </Button>
      </Box>

      {loading ? (
        <CircularProgress color="primary" />
      ) : conflicts.length === 0 ? (
        <Typography color="success.main" fontWeight={600}>
          ✅ No conflicts detected — all resources are properly scheduled.
        </Typography>
      ) : (
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {conflicts.length} conflict{conflicts.length !== 1 ? "s" : ""} found.
          </Typography>
          {conflicts.map((c, i) => (
            <Card key={i} variant="outlined" sx={{ borderLeft: "4px solid", borderColor: "warning.main" }}>
              <CardContent>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                  <Chip label={c.resource_type || c.type} color={typeColor(c.resource_type || c.type)} size="small" />
                  <Typography fontWeight={700} sx={{ color: "text.secondary" }}>
                    {c.resource_id || c.id}
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {c.description || c.message || JSON.stringify(c)}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}
    </Box>
  );
}
