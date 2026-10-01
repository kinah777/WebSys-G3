import { useEffect, useState } from "react";

import {
  ThemeProvider,
  CssBaseline,
  createTheme,
} from "@mui/material";

import RootComponent from "./components/RootComponent";
import LoginPage from "./components/LoginPage";

import {
  Route,
  createBrowserRouter,
  createRoutesFromElements,
  RouterProvider,
} from "react-router-dom";

import Customer from "./components/bodyComponents/customer/Customer";
import Revenue from "./components/bodyComponents/revenue/Revenue";
import Growth from "./components/bodyComponents/growth/Growth";
import Report from "./components/bodyComponents/report/Report";
import Setting from "./components/bodyComponents/Settings/Setting";
import Order from "./components/bodyComponents/order/Order";
import {
  CalendarPage,
  ConflictsPage,
  DashboardPage,
  ForecastPage,
  MaterialsPage,
  MembersPage,
  ProjectsPage,
  ResourcesPage,
  TasksPage,
} from "./components/ConstructionPages";

function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("buildsync_token");
    const storedUser = localStorage.getItem("buildsync_user");
    if (token && storedUser) {
      setAuthenticated(true);
      setUser(JSON.parse(storedUser));
    }
  }, []);

  const handleLogin = (payload) => {
    const nextUser = payload.user;
    localStorage.setItem("buildsync_token", payload.access_token);
    localStorage.setItem("buildsync_user", JSON.stringify(nextUser));
    setUser(nextUser);
    setAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("buildsync_token");
    localStorage.removeItem("buildsync_user");
    setUser(null);
    setAuthenticated(false);
  };

  const theme = createTheme({
    spacing: 4,

    palette: {
      mode: "light",

      primary: {
        main: "#D84A05",
      },

      text: {
        primary: "#ffffff",
        secondary: "#343434",
      },

      secondary: {
        main: "#343434",
      },

      error: {
        main: "#E03137",
      },
    },

    typography: {
      fontFamily: "Montserrat, sans-serif",
    },

    components: {
      MuiCssBaseline: {
        styleOverrides: `
          @font-face {
            font-family: "Montserrat";
            font-style: normal;
            font-display: swap;
            font-weight: 400;
            src: url("/public/static/fonts/static/Montserrat-Regular.ttf") format("truetype");
          }

          body {
            font-family: "Montserrat", sans-serif;
          }
        `,
      },
    },
  });

  const router = createBrowserRouter(
    createRoutesFromElements(
      <Route path="/" element={<RootComponent onLogout={handleLogout} user={user} />}>
        <Route index element={<DashboardPage />} />

        <Route path="home" element={<DashboardPage />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="tasks" element={<TasksPage isAdmin={user?.role === "admin"} />} />
        <Route path="inventory" element={<MaterialsPage />} />
        <Route path="resources" element={<ResourcesPage />} />
        <Route path="conflicts" element={<ConflictsPage />} />
        <Route path="calendar" element={<CalendarPage />} />
        <Route path="members" element={<MembersPage />} />
        <Route path="forecasts" element={<ForecastPage />} />
        <Route path="orders" element={<Order />} />
        <Route path="customers" element={<Customer />} />
        <Route path="revenue" element={<Revenue />} />
        <Route path="growth" element={<Growth />} />
        <Route path="reports" element={<Report />} />
        <Route path="settings" element={<Setting />} />
      </Route>
    )
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {authenticated ? (
        <RouterProvider router={router} />
      ) : (
        <LoginPage onLogin={handleLogin} />
      )}
    </ThemeProvider>
  );
}

export default App;