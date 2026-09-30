import "../../public/styles/links.css";
import {
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Box,
} from "@mui/material";
import {
  DashboardOutlined,
  FolderOpenOutlined,
  AssignmentOutlined,
  Inventory2Outlined,
  BuildOutlined,
  WarningAmberOutlined,
  CalendarMonthOutlined,
  GroupsOutlined,
  QueryStatsOutlined,
} from "@mui/icons-material";
import { useLocation, useNavigate } from "react-router-dom";

export default function SideBarComponent() {
  const navigate = useNavigate();
  const navigateTo = (to) => navigate(to);
  const location = useLocation();
  const currentPage = location.pathname;

  const sideBarComponent = [
    {
      title: "Dashboard",
      path: "/home",
      component: <DashboardOutlined fontSize="medium" color="primary" />,
    },
    {
      title: "Projects",
      path: "/projects",
      component: <FolderOpenOutlined fontSize="medium" color="primary" />,
    },
    {
      title: "Tasks",
      path: "/tasks",
      component: <AssignmentOutlined fontSize="medium" color="primary" />,
    },
    {
      title: "Inventory",
      path: "/inventory",
      component: <Inventory2Outlined fontSize="medium" color="primary" />,
    },
    {
      title: "Resources",
      path: "/resources",
      component: <BuildOutlined fontSize="medium" color="primary" />,
    },
    {
      title: "Conflicts",
      path: "/conflicts",
      component: <WarningAmberOutlined fontSize="medium" color="primary" />,
    },
    {
      title: "Calendar",
      path: "/calendar",
      component: <CalendarMonthOutlined fontSize="medium" color="primary" />,
    },
    {
      title: "Members",
      path: "/members",
      component: <GroupsOutlined fontSize="medium" color="primary" />,
    },
    {
      title: "Forecasts",
      path: "/forecasts",
      component: <QueryStatsOutlined fontSize="medium" color="primary" />,
    },
  ];
  return (
    <List>
      {sideBarComponent.map((comp, index) => (
        <ListItem disablePadding dense={true} key={index}>
          <Box width="100%">
            <ListItemButton
              onClick={() => navigateTo(comp.path)}
              selected={
                currentPage === comp.path ||
                (currentPage === "/" && comp.path === "/home")
              }
              sx={{
                mb: 3,
                borderLeft: 0,
                borderColor: "primary.main",
                ml: 4,
                borderRadius: 3,
              }}
            >
              <ListItemIcon>{comp.component}</ListItemIcon>
              <ListItemText
                primary={comp.title}
                primaryTypographyProps={{
                  fontSize: "medium",
                  fontWeight:
                    currentPage === comp.path ||
                    (currentPage === "/" && comp.path === "/home")
                      ? "bold"
                      : "",
                  color:
                    currentPage === comp.path ||
                    (currentPage === "/" && comp.path === "/home")
                      ? "primary.main"
                      : "inherit",
                }}
              />
            </ListItemButton>
          </Box>
        </ListItem>
      ))}
    </List>
  );
}
