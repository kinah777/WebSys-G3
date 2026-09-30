import myLG from "../BuildSync LG.png";

import {
  Box,
  Grid,
  AppBar,
  Container,
  Typography,
  Paper,
  IconButton,
  Avatar,
  Badge,
  Menu,
  MenuItem,
  Divider,
  ListItemIcon,
  Tooltip,
} from "@mui/material";
import {
  NotificationsOutlined,
  Settings,
  Logout,
  AccountCircleOutlined,
} from "@mui/icons-material";
import { useState } from "react";

export default function NavBarComponent() {
  const [notificationAnchorEl, setNotificationAnchorEl] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  // handleNotificationClicked
  const open = Boolean(anchorEl);
  const notificationOpen = Boolean(notificationAnchorEl);
  const handleAvatarClicked = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handleNotificationClicked = (event) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };
  const notificationHandleClose = () => {
    setNotificationAnchorEl(null);
  };

  return (
    <Grid container>
      <Grid item md={12}>
        <Paper elevation={4} sx={{ borderRadius: 5, overflow: "hidden" }}>
          <AppBar sx={{ padding: 2}} position="sticky">
            <Container maxWidth="xxl">
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <Box
                  variant="h6"
                  component="a"
                  href="/"
                  sx={{
                    mx: 2,
                    display: { xs: "none", md: "flex" },
                    fontWeight: 700,
                    letterSpacing: ".2rem",
                    fontColor: "black",
                    textDecoration: "none",
                  }}
                >
                  <img
                    src={myLG} 
                    alt="Logo"
                    style={{ width: "200px", height: "50px" }} 
                  />
                </Box>

                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "right",
                    alignItems: "center",
                  }}
                >
                  <IconButton color="inherit">
                    <Badge variant="dot" color="error" invisible={false}>
                      <NotificationsOutlined
                        sx={{ width: 32, height: 32 }}
                        onClick={handleNotificationClicked}
                      />
                    </Badge>
                  </IconButton>
                  <Menu
                  
                    open={notificationOpen}
                    anchorEl={notificationAnchorEl}
                    onClick={notificationHandleClose}
                    onClose={notificationHandleClose}

                  >
                    <MenuItem sx={{ fontSize: "small", color: "red" }}>Stock 304 (low stock) </MenuItem>
                    <Divider />
                    <MenuItem sx={{ fontSize: "small", color: "black" }}>Upcoming Delivery no. 34</MenuItem>
                    <MenuItem sx={{ fontSize: "small", color: "black" }}>Delivery Successful no. 67</MenuItem>
                  </Menu>
                  <IconButton
                    onClick={handleAvatarClicked}
                    size="small"
                    sx={{ mx: 2 }}
                    aria-haspopup="true"
                  >
                    <Tooltip title="account settings">
                      <Avatar sx={{ width: 32, height: 32, color: "white" }}>A</Avatar>
                    </Tooltip>
                  </IconButton>
                  <Typography fontFamily={"Montserrat"}>ADMIN</Typography>
                </Box>

                <Menu
                  open={open}
                  anchorEl={anchorEl}
                  onClick={handleClose}
                  onClose={handleClose}
                >
                  <MenuItem sx={{ color: "black" }}>
                    <ListItemIcon> 
                      <AccountCircleOutlined fontSize="small" sx={{ color: "black" }} />
                    </ListItemIcon > 
                    Profile 
                  </MenuItem>
                  <Divider />

                  <MenuItem sx={{ color: "black" }}>
                    <ListItemIcon>
                      <Settings fontSize="small" sx={{ color: "black" }} />
                    </ListItemIcon>
                    Settings
                  </MenuItem>
                  <MenuItem sx={{ color: "black" }}>
                    <ListItemIcon>
                      <Logout fontSize="small" sx={{ color: "black" }} />
                    </ListItemIcon>
                    Logout
                  </MenuItem>
                </Menu>
              </Box>
            </Container>
          </AppBar>
        </Paper>
      </Grid>
    </Grid>
  );
}

{
  /* <Grid item md={7}>
                  <Paper
                    component="form"
                    sx={{
                      p: "2px 4px",
                      width: "50%",
                      mx: "auto",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <InputBase
                      sx={{ ml: 1, flex: 1 }}
                      placeholder="Search "
                      inputProps={{ "aria-label": "search" }}
                    />
                    <IconButton
                      type="button"
                      sx={{ p: "10px" }}
                      aria-label="search"
                    >
                      <Search />
                    </IconButton>
                  </Paper>
                </Grid> */
}
