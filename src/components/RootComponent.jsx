import React from "react";
import NavBarComponent from "./NavBarComponent";
import { Box, Grid } from "@mui/material";
import SideBarComponent from "./SideBarComponent";
import { Outlet } from "react-router-dom";
import myBG from "../BuildSync BG.png";

export default function RootComponent() {
  return (
    <>
      <NavBarComponent />
      <Box
        sx={
          {
          minHeight: "calc(100vh - 64px)",
          width: "100%",
          backgroundImage: `url("${myBG}")`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat", 
          }
        }
      >
        <Grid container spacing={0}>
          <Grid item md={2} sm={0}>
            <SideBarComponent />
          </Grid>
          <Grid item md={10}>
            <Outlet />
          </Grid>
        </Grid>
      </Box>
    </>
  );
}
