import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  MenuItem,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { apiRequest } from "../api";

function useApiCollection(endpoint) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    apiRequest(endpoint, { signal: controller.signal })
      .then((result) => setRows(Array.isArray(result) ? result : []))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [endpoint, reloadKey]);

  return { rows, loading, error, reload: () => setReloadKey((key) => key + 1) };
}

function ApiCollectionPage({
  title,
  description,
  endpoint,
  idField,
  fields = [],
  columns,
  canCreate = true,
  canEdit = true,
  canDelete = true,
}) {
  const { rows, loading, error, reload } = useApiCollection(endpoint);
  const [formValues, setFormValues] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState("");
  const [optionsByPath, setOptionsByPath] = useState({});
  const optionPaths = [...new Set(fields.map((field) => field.optionsPath).filter(Boolean))];
  const optionPathKey = optionPaths.join("|");

  useEffect(() => {
    const controller = new AbortController();
    optionPaths.forEach((path) => {
      apiRequest(path, { signal: controller.signal })
        .then((options) => {
          setOptionsByPath((current) => ({ ...current, [path]: options }));
        })
        .catch(() => {});
    });
    return () => controller.abort();
  }, [optionPathKey]);

  const resetForm = () => {
    setFormValues(Object.fromEntries(fields.map((field) => [field.name, field.defaultValue ?? ""])));
    setEditingId(null);
    setActionError("");
  };

  const openCreate = () => {
    resetForm();
    setFormOpen(true);
  };

  const openEdit = (row) => {
    setFormValues(Object.fromEntries(fields.map((field) => [field.name, row[field.name] ?? ""])));
    setEditingId(row[idField]);
    setActionError("");
    setFormOpen(true);
  };

  const submitForm = async (event) => {
    event.preventDefault();
    setSaving(true);
    setActionError("");
    const payload = {};
    fields.forEach((field) => {
      const value = formValues[field.name];
      if (value === "" || value === undefined) return;
      payload[field.name] = field.type === "number" ? Number(value) : value;
    });

    try {
      await apiRequest(editingId ? `${endpoint}/${editingId}` : endpoint, {
        method: editingId ? "PATCH" : "POST",
        body: payload,
      });
      setFormOpen(false);
      resetForm();
      reload();
    } catch (requestError) {
      setActionError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

  const deleteRow = async (row) => {
    if (!window.confirm(`Delete ${row[idField]}?`)) return;
    setActionError("");
    try {
      await apiRequest(`${endpoint}/${row[idField]}`, { method: "DELETE" });
      reload();
    } catch (requestError) {
      setActionError(requestError.message);
    }
  };

  const gridColumns = [
    ...columns,
    ...(canEdit || canDelete
      ? [{
          field: "actions",
          headerName: "Actions",
          width: 150,
          sortable: false,
          renderCell: ({ row }) => (
            <Stack direction="row" spacing={1}>
              {canEdit && <Button size="small" onClick={() => openEdit(row)}>Edit</Button>}
              {canDelete && <Button size="small" color="error" onClick={() => deleteRow(row)}>Delete</Button>}
            </Stack>
          ),
        }]
      : []),
  ];

  return (
    <Stack spacing={2.5} sx={{ p: { xs: 2, md: 3 } }}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 2 }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>{title}</Typography>
          {description && <Typography color="text.secondary" sx={{ mt: 0.5 }}>{description}</Typography>}
        </Box>
        {canCreate && <Button variant="contained" onClick={formOpen ? () => setFormOpen(false) : openCreate}>{formOpen ? "Close form" : `Add ${title.replace(/s$/, "")}`}</Button>}
      </Box>
      {(error || actionError) && <Alert severity="error">{actionError || error}</Alert>}
      {formOpen && (
        <Paper component="form" onSubmit={submitForm} variant="outlined" sx={{ p: 2 }}>
          <Typography variant="subtitle1" fontWeight={700} mb={1.5}>{editingId ? `Edit ${title}` : `New ${title.replace(/s$/, "")}`}</Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" }, gap: 1.5 }}>
            {fields.map((field) => (
              <TextField
                key={field.name}
                label={field.label}
                type={field.type === "number" ? "number" : field.type === "date" ? "date" : "text"}
                value={formValues[field.name] ?? ""}
                required={field.required && !editingId}
                onChange={(event) => setFormValues((current) => ({ ...current, [field.name]: event.target.value }))}
                select={field.type === "select"}
                fullWidth
                size="small"
                InputLabelProps={field.type === "date" ? { shrink: true } : undefined}
                inputProps={field.type === "number" ? { min: field.min ?? 0, step: field.step ?? "any" } : undefined}
              >
                {field.type === "select" && (field.options || (optionsByPath[field.optionsPath] || []).map((option) => ({
                  value: option[field.optionValue],
                  label: option[field.optionLabel],
                }))).map((option) => <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>)}
              </TextField>
            ))}
          </Box>
          <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
            <Button type="submit" variant="contained" disabled={saving}>{saving ? "Saving..." : editingId ? "Save changes" : "Create"}</Button>
            <Button onClick={() => { setFormOpen(false); resetForm(); }}>Cancel</Button>
          </Stack>
        </Paper>
      )}
      <Box sx={{ height: 440, width: "100%" }}>
        {loading ? <CircularProgress /> : (
          <DataGrid
            rows={rows}
            columns={gridColumns}
            getRowId={(row) => row[idField]}
            pageSizeOptions={[10, 25, 50]}
            initialState={{ pagination: { paginationModel: { page: 0, pageSize: 10 } } }}
            disableRowSelectionOnClick
          />
        )}
      </Box>
    </Stack>
  );
}

const projectFields = [
  { name: "project_name", label: "Project name", required: true },
  { name: "project_type", label: "Project type" },
  { name: "location", label: "Location" },
  { name: "start_date", label: "Start date", type: "date" },
  { name: "end_date", label: "End date", type: "date" },
  { name: "budget", label: "Budget (PHP)", type: "number" },
  { name: "priority", label: "Priority", type: "select", options: ["Critical", "High", "Medium", "Low"].map((value) => ({ value, label: value })) },
  { name: "status", label: "Status", type: "select", defaultValue: "Planning", options: ["Planning", "Ongoing", "Completed", "On Hold"].map((value) => ({ value, label: value })) },
];

const projectColumns = [
  { field: "project_id", headerName: "ID", width: 110 },
  { field: "project_name", headerName: "Project", minWidth: 200, flex: 1 },
  { field: "location", headerName: "Location", minWidth: 140, flex: 1 },
  { field: "start_date", headerName: "Start", width: 120 },
  { field: "end_date", headerName: "End", width: 120 },
  { field: "status", headerName: "Status", width: 130 },
  { field: "completion_percentage", headerName: "Progress %", width: 120 },
];

export function ProjectsPage() {
  return <ApiCollectionPage title="Projects" description="Create and manage construction projects." endpoint="/projects" idField="project_id" fields={projectFields} columns={projectColumns} />;
}

const taskFields = [
  { name: "project_id", label: "Project", type: "select", required: true, optionsPath: "/projects", optionValue: "project_id", optionLabel: "project_name" },
  { name: "task_name", label: "Task name", required: true },
  { name: "start_date", label: "Start date", type: "date" },
  { name: "end_date", label: "End date", type: "date" },
  { name: "duration_days", label: "Duration (days)", type: "number" },
  { name: "dependency", label: "Depends on" },
  { name: "status", label: "Status", type: "select", defaultValue: "Pending", options: ["Pending", "Not Started", "In Progress", "Completed"].map((value) => ({ value, label: value })) },
];

const taskColumns = [
  { field: "schedule_id", headerName: "ID", width: 110 },
  { field: "project_id", headerName: "Project", width: 120 },
  { field: "task_name", headerName: "Task", minWidth: 200, flex: 1 },
  { field: "start_date", headerName: "Start", width: 120 },
  { field: "end_date", headerName: "End", width: 120 },
  { field: "status", headerName: "Status", width: 140 },
];

export function TasksPage() {
  return <ApiCollectionPage title="Tasks" description="Schedule project milestones and update task status." endpoint="/project-schedules" idField="schedule_id" fields={taskFields} columns={taskColumns} />;
}

const materialFields = [
  { name: "name", label: "Item name", required: true },
  { name: "type", label: "Category" },
  { name: "unit", label: "Unit (bags, tons, etc.)" },
  { name: "quantity_in_stock", label: "Quantity", type: "number", defaultValue: 0 },
  { name: "reorder_level", label: "Minimum stock", type: "number", defaultValue: 0 },
  { name: "unit_cost", label: "Unit cost (PHP)", type: "number", defaultValue: 0 },
];

const materialColumns = [
  { field: "material_id", headerName: "ID", width: 110 },
  { field: "name", headerName: "Item", minWidth: 190, flex: 1 },
  { field: "type", headerName: "Category", minWidth: 140, flex: 1 },
  { field: "quantity_in_stock", headerName: "Quantity", width: 130 },
  { field: "unit", headerName: "Unit", width: 100 },
  { field: "reorder_level", headerName: "Minimum stock", width: 140 },
  { field: "unit_cost", headerName: "Unit cost", width: 130 },
];

export function MaterialsPage() {
  return <ApiCollectionPage title="Inventory" description="Construction materials, stock levels, and reorder thresholds." endpoint="/materials" idField="material_id" fields={materialFields} columns={materialColumns} />;
}

const equipmentFields = [
  { name: "name", label: "Equipment name", required: true },
  { name: "type", label: "Category" },
  { name: "model", label: "Model" },
  { name: "status", label: "Status", type: "select", defaultValue: "Available", options: ["Available", "In Use", "Maintenance", "Under Maintenance", "Retired"].map((value) => ({ value, label: value })) },
];

const equipmentColumns = [
  { field: "equipment_id", headerName: "ID", width: 120 },
  { field: "name", headerName: "Equipment", minWidth: 200, flex: 1 },
  { field: "type", headerName: "Category", minWidth: 140, flex: 1 },
  { field: "model", headerName: "Model", minWidth: 130, flex: 1 },
  { field: "status", headerName: "Status", width: 150 },
];

const vehicleFields = [
  { name: "plate_number", label: "Plate number", required: true },
  { name: "vehicle_type", label: "Vehicle type" },
  { name: "driver", label: "Driver" },
  { name: "status", label: "Status", type: "select", defaultValue: "Available", options: ["Available", "In Use", "Maintenance", "Under Maintenance", "Retired"].map((value) => ({ value, label: value })) },
];

const vehicleColumns = [
  { field: "vehicle_id", headerName: "ID", width: 120 },
  { field: "plate_number", headerName: "Plate", width: 140 },
  { field: "vehicle_type", headerName: "Vehicle", minWidth: 180, flex: 1 },
  { field: "driver", headerName: "Driver", minWidth: 150, flex: 1 },
  { field: "status", headerName: "Status", width: 150 },
];

function AssetTab({ title, endpoint, idField, fields, columns }) {
  return <ApiCollectionPage title={title} endpoint={endpoint} idField={idField} fields={fields} columns={columns} />;
}

const assignmentTabs = [
  {
    label: "Equipment",
    title: "Equipment assignments",
    endpoint: "/equipment-allocations",
    idField: "allocation_id",
    assetEndpoint: "/equipment",
    assetId: "equipment_id",
    assetLabel: "name",
    resourceKey: "equipment_id",
    columns: ["allocation_id", "project_id", "equipment_id", "start_date", "end_date", "allocation_status"],
  },
  {
    label: "Vehicles",
    title: "Vehicle assignments",
    endpoint: "/vehicle-allocations",
    idField: "vehicle_allocation_id",
    assetEndpoint: "/vehicles",
    assetId: "vehicle_id",
    assetLabel: "plate_number",
    resourceKey: "vehicle_id",
    columns: ["vehicle_allocation_id", "project_id", "vehicle_id", "start_date", "end_date", "allocation_status"],
  },
  {
    label: "Employees",
    title: "Employee assignments",
    endpoint: "/employee-allocations",
    idField: "employee_allocation_id",
    assetEndpoint: "/employees",
    assetId: "employee_id",
    assetLabel: "name",
    resourceKey: "employee_id",
    columns: ["employee_allocation_id", "project_id", "employee_id", "start_date", "end_date", "allocation_status"],
  },
  {
    label: "Materials",
    title: "Material assignments",
    endpoint: "/material-allocations",
    idField: "material_allocation_id",
    assetEndpoint: "/materials",
    assetId: "material_id",
    assetLabel: "name",
    resourceKey: "material_id",
    columns: ["material_allocation_id", "project_id", "material_id", "quantity_required", "required_date", "status"],
  },
];

function AssignmentTab({ config }) {
  const fields = [
    { name: "project_id", label: "Project", type: "select", required: true, optionsPath: "/projects", optionValue: "project_id", optionLabel: "project_name" },
    { name: config.resourceKey, label: config.label.slice(0, -1), type: "select", required: true, optionsPath: config.assetEndpoint, optionValue: config.assetId, optionLabel: config.assetLabel },
    ...(config.label === "Materials"
      ? [
          { name: "quantity_required", label: "Quantity required", type: "number", required: true },
          { name: "quantity_used", label: "Quantity used", type: "number", defaultValue: 0 },
          { name: "required_date", label: "Required date", type: "date" },
          { name: "status", label: "Status", type: "select", defaultValue: "Scheduled", options: ["Scheduled", "Active", "Completed", "Cancelled"].map((value) => ({ value, label: value })) },
        ]
      : [
          { name: "start_date", label: "Start date", type: "date", required: true },
          { name: "end_date", label: "End date", type: "date", required: true },
          ...(config.label === "Equipment" || config.label === "Vehicles" ? [{ name: "purpose", label: "Purpose" }] : [{ name: "role", label: "Assignment role" }]),
          { name: "allocation_status", label: "Status", type: "select", defaultValue: "Scheduled", options: ["Scheduled", "Active", "Completed", "Cancelled"].map((value) => ({ value, label: value })) },
        ]),
  ];
  const columns = config.columns.map((field) => ({ field, headerName: field.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()), minWidth: 140, flex: field === config.idField ? 0 : 1, width: field === config.idField ? 170 : undefined }));
  return <ApiCollectionPage title={config.title} description="Bookings are validated by the API for stock availability and scheduling conflicts." endpoint={config.endpoint} idField={config.idField} fields={fields} columns={columns} canEdit={config.label !== "Materials"} />;
}

export function ResourcesPage() {
  const [assignmentTab, setAssignmentTab] = useState(0);
  const [catalogTab, setCatalogTab] = useState(0);
  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Typography variant="h5" fontWeight={700}>Resource assignments</Typography>
      <Typography color="text.secondary" sx={{ mt: 0.5 }}>Assign equipment, vehicles, employees, and materials to projects.</Typography>
      <Tabs value={assignmentTab} onChange={(_, value) => setAssignmentTab(value)} variant="scrollable" sx={{ mt: 2 }}>
        {assignmentTabs.map((item) => <Tab key={item.label} label={item.label} />)}
      </Tabs>
      <AssignmentTab config={assignmentTabs[assignmentTab]} />
      <Typography variant="subtitle1" fontWeight={700} sx={{ mt: 2 }}>Asset catalog</Typography>
      <Tabs value={catalogTab} onChange={(_, value) => setCatalogTab(value)} sx={{ mt: 1 }}>
        <Tab label="Equipment catalog" />
        <Tab label="Vehicle catalog" />
      </Tabs>
      {catalogTab === 0 ? <AssetTab title="Equipment" endpoint="/equipment" idField="equipment_id" fields={equipmentFields} columns={equipmentColumns} /> : <AssetTab title="Vehicles" endpoint="/vehicles" idField="vehicle_id" fields={vehicleFields} columns={vehicleColumns} />}
    </Box>
  );
}

export function MembersPage() {
  const employeeFields = [
    { name: "name", label: "Name", required: true },
    { name: "position", label: "Position" },
    { name: "skill", label: "Skill / trade" },
    { name: "phone", label: "Phone" },
    { name: "employment_status", label: "Status", type: "select", defaultValue: "Active", options: ["Active", "Inactive", "On Leave"].map((value) => ({ value, label: value })) },
  ];
  const employeeColumns = [
    { field: "employee_id", headerName: "ID", width: 120 },
    { field: "name", headerName: "Name", minWidth: 180, flex: 1 },
    { field: "position", headerName: "Position", minWidth: 160, flex: 1 },
    { field: "skill", headerName: "Trade", minWidth: 150, flex: 1 },
    { field: "employment_status", headerName: "Employment status", width: 170 },
  ];
  return (
    <>
      <Alert severity="info" sx={{ m: 3, mb: 0 }}>The API manages employee records, but it does not provide login roles or role-based permissions yet.</Alert>
      <ApiCollectionPage title="Members" description="Manage workforce records and trades." endpoint="/employees" idField="employee_id" fields={employeeFields} columns={employeeColumns} />
    </>
  );
}

export function CalendarPage() {
  const calendarColumns = [
    { field: "schedule_id", headerName: "ID", width: 110 },
    { field: "project_id", headerName: "Project", width: 130 },
    { field: "task_name", headerName: "Task", minWidth: 220, flex: 1 },
    { field: "start_date", headerName: "Start", width: 140 },
    { field: "end_date", headerName: "End", width: 140 },
    { field: "status", headerName: "Status", width: 140 },
  ];
  return <ApiCollectionPage title="Project calendar" description="Schedule view of task start and end dates." endpoint="/project-schedules" idField="schedule_id" columns={calendarColumns} canCreate={false} canEdit={false} canDelete={false} />;
}

export function ForecastPage() {
  const forecastColumns = [
    { field: "project_name", headerName: "Project", minWidth: 200, flex: 1 },
    { field: "daily_burn_rate", headerName: "Daily spend", width: 150 },
    { field: "projected_total_cost", headerName: "Projected cost", width: 170 },
    { field: "projected_overrun", headerName: "Projected overrun", width: 180 },
    { field: "is_overrun", headerName: "Over budget", width: 130 },
  ];
  return (
    <>
      <Alert severity="info" sx={{ m: 3, mb: 0 }}>The connected forecast is project cost forecasting. Material-demand ARIMA forecasts require historical consumption data and a backend endpoint, which are not currently available.</Alert>
      <ApiCollectionPage title="Cost forecasts" description="Projected project spend based on current daily burn rates." endpoint="/financials/forecast" idField="budget_id" columns={forecastColumns} canCreate={false} canEdit={false} canDelete={false} />
    </>
  );
}

export function ConflictsPage() {
  const [conflicts, setConflicts] = useState({ equipment: [], employees: [], vehicles: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    Promise.all(["equipment", "employees", "vehicles"].map((type) => apiRequest(`/conflicts/${type}`, { signal: controller.signal })))
      .then(([equipment, employees, vehicles]) => setConflicts({ equipment, employees, vehicles }))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [reloadKey]);

  const cancelAllocation = async (type, allocationId) => {
    setError("");
    setNotice("");
    try {
      await apiRequest("/conflicts/resolve/cancel", { method: "POST", body: { allocation_type: type, allocation_id: allocationId } });
      setNotice(`Allocation ${allocationId} cancelled.`);
      setReloadKey((key) => key + 1);
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  const sections = [
    { key: "equipment", title: "Equipment", idField: "equipment_id", labelField: "equipment_name" },
    { key: "employees", title: "Employees", idField: "employee_id", labelField: "employee_name" },
    { key: "vehicles", title: "Vehicles", idField: "vehicle_id", labelField: "vehicle_plate" },
  ];

  return (
    <Stack spacing={2.5} sx={{ p: { xs: 2, md: 3 } }}>
      <Box>
        <Typography variant="h5" fontWeight={700}>Resource conflicts</Typography>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>Overlapping active bookings detected by the backend.</Typography>
      </Box>
      {error && <Alert severity="error">{error}</Alert>}
      {notice && <Alert severity="success">{notice}</Alert>}
      {loading ? <CircularProgress /> : sections.map((section) => (
        <Box key={section.key}>
          <Typography variant="h6" mb={1}>{section.title} ({conflicts[section.key].length})</Typography>
          <Box sx={{ height: 330 }}>
            <DataGrid
              rows={conflicts[section.key]}
              getRowId={(row) => row.allocation_a}
              columns={[
                { field: section.idField, headerName: "Resource ID", width: 140 },
                { field: section.labelField, headerName: "Resource", minWidth: 180, flex: 1 },
                { field: "project_a", headerName: "Project A", width: 130 },
                { field: "a_start", headerName: "A starts", width: 130 },
                { field: "a_end", headerName: "A ends", width: 130 },
                { field: "project_b", headerName: "Project B", width: 130 },
                { field: "b_start", headerName: "B starts", width: 130 },
                { field: "b_end", headerName: "B ends", width: 130 },
                { field: "resolve", headerName: "Action", width: 170, sortable: false, renderCell: ({ row }) => (
                  <Button size="small" color="error" onClick={() => cancelAllocation(section.key === "employees" ? "employee" : section.key === "vehicles" ? "vehicle" : "equipment", row.allocation_b)}>Cancel booking B</Button>
                ) },
              ]}
              pageSizeOptions={[5, 10]}
              initialState={{ pagination: { paginationModel: { page: 0, pageSize: 5 } } }}
              disableRowSelectionOnClick
            />
          </Box>
        </Box>
      ))}
    </Stack>
  );
}

export function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      apiRequest("/projects", { signal: controller.signal }),
      apiRequest("/materials", { signal: controller.signal }),
      apiRequest("/equipment", { signal: controller.signal }),
      apiRequest("/conflicts/summary", { signal: controller.signal }),
      apiRequest("/financials/summary", { signal: controller.signal }),
    ])
      .then(([projects, materials, equipment, conflicts, finances]) => setSummary({
        projects,
        lowStock: materials.filter((material) => Number(material.quantity_in_stock) <= Number(material.reorder_level)).length,
        availableEquipment: equipment.filter((item) => item.status === "Available").length,
        conflicts,
        finances,
      }))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  const metrics = summary ? [
    ["Active projects", summary.projects.filter((project) => project.status === "Ongoing").length],
    ["Low-stock materials", summary.lowStock],
    ["Available equipment", summary.availableEquipment],
    ["Resource conflicts", summary.conflicts.total],
    ["Budget overruns", summary.finances.overrun_count],
  ] : [];

  return (
    <Stack spacing={2.5} sx={{ p: { xs: 2, md: 3 } }}>
      <Box>
        <Typography variant="h5" fontWeight={700}>Dashboard</Typography>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>Construction operations overview from live backend data.</Typography>
      </Box>
      {error && <Alert severity="error">{error} Check that FastAPI and PostgreSQL are running.</Alert>}
      {loading ? <CircularProgress /> : (
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr 1fr", lg: "repeat(5, minmax(0, 1fr))" }, gap: 1.5 }}>
          {metrics.map(([label, value]) => (
            <Paper key={label} variant="outlined" sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">{label}</Typography>
              <Typography variant="h4" fontWeight={700} sx={{ mt: 1 }}>{value}</Typography>
            </Paper>
          ))}
        </Box>
      )}
      <Alert severity="info">Material-demand predictions are not included yet; the backend currently provides project cost forecasts only.</Alert>
    </Stack>
  );
}