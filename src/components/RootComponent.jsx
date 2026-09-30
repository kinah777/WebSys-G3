import React from "react";
import NavBarComponent from "./NavBarComponent";
import { Box, Grid } from "@mui/material";
import SideBarComponent from "./SideBarComponent";
import { Outlet } from "react-router-dom";
import myBG from "../BuildSync BG.png";
import WavyRippleBackground from "./lightswind/wavy-ripple-background";

export default function RootComponent() {
  return (
    <Box
      sx={{
        position: "relative",
        isolation: "isolate",
        minHeight: "100vh",
        width: "100%",
        backgroundImage: `url("${myBG}")`,
        backgroundSize: "cover",
        backgroundAttachment: "fixed",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      <WavyRippleBackground
        className="app-background-ripple"
        waveColor="#ff9000"
        backgroundColor="transparent"
        speed={0.32}
        frequency={3.5}
        ringSharpness={0.55}
        maxOpacity={1.34}
      />
      <Box sx={{ position: "relative", zIndex: 1 }}>
        <Box sx={{ pt: 3, px: { xs: 2, md: 3 } }}>
          <NavBarComponent />
        </Box>
        <Grid container spacing={0}>
          <Grid item md={2} sm={0}>
            <SideBarComponent />
          </Grid>
          <Grid item md={10}>
            <Outlet />
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}
