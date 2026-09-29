import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Chip,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";
import { ChevronLeft, ChevronRight } from "@mui/icons-material";
import PropTypes from "prop-types";
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
  allowTaskAssignments = false,
}) {
  const { rows, loading, error, reload } = useApiCollection(endpoint);
  const [formValues, setFormValues] = useState({});
  const [editingId, setEditingId] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState("");
  const [selectedTask, setSelectedTask] = useState(null);
  const [optionsByPath, setOptionsByPath] = useState({});
  const optionPathKey = [...new Set(fields.map((field) => field.optionsPath).filter(Boolean))].join("|");

  useEffect(() => {
    const controller = new AbortController();
    optionPathKey.split("|").filter(Boolean).forEach((path) => {
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
    ...(canEdit || canDelete || allowTaskAssignments
      ? [{
          field: "actions",
          headerName: "Actions",
          width: allowTaskAssignments ? 280 : 150,
          sortable: false,
          renderCell: ({ row }) => (
            <Stack direction="row" spacing={1}>
              {canEdit && <Button size="small" onClick={() => openEdit(row)}>Edit</Button>}
              {canDelete && <Button size="small" color="error" onClick={() => deleteRow(row)}>Delete</Button>}
              {allowTaskAssignments && <Button size="small" onClick={() => setSelectedTask(row)}>Assign resources</Button>}
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
      {allowTaskAssignments && selectedTask && (
        <TaskAssignmentsPanel task={selectedTask} onClose={() => setSelectedTask(null)} />
      )}
    </Stack>
  );
}

ApiCollectionPage.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
  endpoint: PropTypes.string.isRequired,
  idField: PropTypes.string.isRequired,
  fields: PropTypes.array,
  columns: PropTypes.array.isRequired,
  canCreate: PropTypes.bool,
  canEdit: PropTypes.bool,
  canDelete: PropTypes.bool,
  allowTaskAssignments: PropTypes.bool,
};

function TaskAssignmentsPanel({ task, onClose }) {
  const endpoint = `/project-schedules/${task.schedule_id}/assignments`;
  const { rows: assignments, loading, error, reload } = useApiCollection(endpoint);
  const { rows: employees } = useApiCollection("/employees");
  const { rows: equipment } = useApiCollection("/equipment");
  const { rows: vehicles } = useApiCollection("/vehicles");
  const { rows: materials } = useApiCollection("/materials");
  const [resourceType, setResourceType] = useState("employee");
  const [resourceId, setResourceId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState("");
  const resourcesByType = { employee: employees, equipment, vehicle: vehicles, material: materials };
  const idByType = { employee: "employee_id", equipment: "equipment_id", vehicle: "vehicle_id", material: "material_id" };
  const labelByType = { employee: "name", equipment: "name", vehicle: "plate_number", material: "name" };
  const availableResources = resourcesByType[resourceType];

  const addAssignment = async (event) => {
    event.preventDefault();
    setSaving(true);
    setActionError("");
    try {
      await apiRequest(endpoint, {
        method: "POST",
        body: {
          resource_type: resourceType,
          resource_id: resourceId,
          ...(resourceType === "material" ? { quantity: Number(quantity) } : {}),
        },
      });
      setResourceId("");
      setQuantity("");
      reload();
    } catch (requestError) {
      setActionError(requestError.message);
    } finally {
      setSaving(false);
    }
  };

  const removeAssignment = async (assignment) => {
    try {
      await apiRequest(`${endpoint}/${assignment.assignment_id}`, { method: "DELETE" });
      reload();
    } catch (requestError) {
      setActionError(requestError.message);
    }
  };

  return (
    <Paper variant="outlined" sx={{ p: 2 }}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" gap={2}>
        <Box>
          <Typography variant="h6">Task resources</Typography>
          <Typography color="text.secondary">{task.task_name} · {task.schedule_id}</Typography>
        </Box>
        <Button onClick={onClose}>Close</Button>
      </Stack>
      {(error || actionError) && <Alert severity="error" sx={{ my: 1 }}>{actionError || error}</Alert>}
      <Box component="form" onSubmit={addAssignment} sx={{ display: "flex", flexWrap: "wrap", gap: 1.5, mt: 2 }}>
        <TextField select size="small" label="Resource type" value={resourceType} onChange={(event) => { setResourceType(event.target.value); setResourceId(""); }} sx={{ minWidth: 150 }}>
          <MenuItem value="employee">Employee</MenuItem>
          <MenuItem value="equipment">Equipment</MenuItem>
          <MenuItem value="vehicle">Vehicle</MenuItem>
          <MenuItem value="material">Material</MenuItem>
        </TextField>
        <TextField select size="small" label="Resource" required value={resourceId} onChange={(event) => setResourceId(event.target.value)} sx={{ minWidth: 220, flexGrow: 1 }}>
          {availableResources.map((resource) => {
            const id = resource[idByType[resourceType]];
            return <MenuItem key={id} value={id}>{resource[labelByType[resourceType]]} ({id})</MenuItem>;
          })}
        </TextField>
        {resourceType === "material" && <TextField size="small" label="Quantity" required type="number" inputProps={{ min: 0.01, step: "any" }} value={quantity} onChange={(event) => setQuantity(event.target.value)} />}
        <Button type="submit" variant="contained" disabled={saving}>{saving ? "Assigning..." : "Assign"}</Button>
      </Box>
      {loading ? <CircularProgress sx={{ mt: 2 }} /> : (
        <Stack spacing={1} sx={{ mt: 2 }}>
          {assignments.length === 0 && <Typography color="text.secondary">No resources assigned to this task.</Typography>}
          {assignments.map((assignment) => (
            <Paper key={assignment.assignment_id} variant="outlined" sx={{ p: 1, display: "flex", alignItems: "center", gap: 1 }}>
              <Chip size="small" label={assignment.resource_type} />
              <Typography sx={{ flexGrow: 1 }}>{assignment.resource_name} ({assignment.resource_id}){assignment.quantity ? ` · ${assignment.quantity}` : ""}</Typography>
              <Button size="small" color="error" onClick={() => removeAssignment(assignment)}>Remove</Button>
            </Paper>
          ))}
        </Stack>
      )}
    </Paper>
  );
}

TaskAssignmentsPanel.propTypes = {
  task: PropTypes.object.isRequired,
  onClose: PropTypes.func.isRequired,
};

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
  return <ApiCollectionPage title="Tasks" description="Schedule project milestones, update task status, and assign resources directly to tasks." endpoint="/project-schedules" idField="schedule_id" fields={taskFields} columns={taskColumns} allowTaskAssignments />;
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

AssetTab.propTypes = {
  title: PropTypes.string.isRequired,
  endpoint: PropTypes.string.isRequired,
  idField: PropTypes.string.isRequired,
  fields: PropTypes.array.isRequired,
  columns: PropTypes.array.isRequired,
};

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

AssignmentTab.propTypes = {
  config: PropTypes.object.isRequired,
};

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
  const { rows: tasks, loading, error } = useApiCollection("/project-schedules");
  const { rows: projects } = useApiCollection("/projects");
  const [visibleMonth, setVisibleMonth] = useState(() => new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const monthTitle = visibleMonth.toLocaleDateString(undefined, { month: "long", year: "numeric" });
  const firstOfMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1);
  const gridStart = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth(), 1 - ((firstOfMonth.getDay() + 6) % 7));
  const days = Array.from({ length: 42 }, (_, index) => new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + index));
  const today = new Date();
  const todayKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  const projectNames = Object.fromEntries(projects.map((project) => [project.project_id, project.project_name]));
  const tasksWithDates = tasks.filter((task) => task.start_date && task.end_date);
  const hasUndatedTasks = tasks.some((task) => !task.start_date || !task.end_date);

  return (
    <Stack spacing={2} sx={{ p: { xs: 1.5, md: 3 } }}>
      <Box sx={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: 1 }}>
        <Box>
          <Typography variant="h5" fontWeight={700}>Project calendar</Typography>
          <Typography color="text.secondary">Tasks shown across their scheduled date range.</Typography>
        </Box>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Button onClick={() => setVisibleMonth(new Date(new Date().getFullYear(), new Date().getMonth(), 1))}>Today</Button>
          <IconButton aria-label="Previous month" onClick={() => setVisibleMonth(new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1))}><ChevronLeft /></IconButton>
          <Typography variant="h6" sx={{ minWidth: 150, textAlign: "center" }}>{monthTitle}</Typography>
          <IconButton aria-label="Next month" onClick={() => setVisibleMonth(new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1))}><ChevronRight /></IconButton>
        </Stack>
      </Box>
      {error && <Alert severity="error">{error}</Alert>}
      {hasUndatedTasks && <Alert severity="info">Tasks without both a start and end date are not placed on the calendar.</Alert>}
      {loading ? <CircularProgress /> : (
        <Box sx={{ overflowX: "auto" }}>
          <Box sx={{ minWidth: 760 }}>
            <Box sx={{ display: "grid", gridTemplateColumns: "repeat(7, minmax(0, 1fr))", gap: 0.5, mb: 0.5 }}>
              {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => (
                <Typography key={day} variant="caption" fontWeight={700} sx={{ px: 1, py: 0.5 }}>{day}</Typography>
              ))}
            </Box>
            <Box sx={{ display: "grid", gridTemplateColumns: "repeat(7, minmax(0, 1fr))", gap: 0.5 }}>
              {days.map((day) => {
                const dayKey = `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`;
                const todaysTasks = tasksWithDates.filter((task) => task.start_date <= dayKey && task.end_date >= dayKey);
                const isCurrentMonth = day.getMonth() === visibleMonth.getMonth();
                const isToday = dayKey === todayKey;
                return (
                  <Paper key={dayKey} variant="outlined" sx={{ minHeight: 128, p: 0.75, overflow: "hidden", bgcolor: isCurrentMonth ? "background.paper" : "action.hover", borderColor: isToday ? "primary.main" : "divider" }}>
                    <Typography variant="caption" fontWeight={isToday ? 700 : 400} color={isCurrentMonth ? "text.primary" : "text.disabled"}>{day.getDate()}</Typography>
                    <Stack spacing={0.5} sx={{ mt: 0.5 }}>
                      {todaysTasks.slice(0, 3).map((task) => (
                        <Box key={task.schedule_id} title={`${task.task_name} · ${projectNames[task.project_id] || task.project_id}`} sx={{ px: 0.75, py: 0.5, bgcolor: task.status === "Completed" ? "success.light" : task.status === "In Progress" ? "warning.light" : "primary.light", color: "#20252b", borderRadius: 0.75, overflow: "hidden" }}>
                          <Typography variant="caption" fontWeight={700} noWrap display="block">{task.task_name}</Typography>
                          <Typography variant="caption" noWrap display="block">{projectNames[task.project_id] || task.project_id}</Typography>
                        </Box>
                      ))}
                      {todaysTasks.length > 3 && <Typography variant="caption" color="text.secondary">+{todaysTasks.length - 3} more</Typography>}
                    </Stack>
                  </Paper>
                );
              })}
            </Box>
          </Box>
        </Box>
      )}
    </Stack>
  );
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