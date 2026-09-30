import { SparkleParticles } from "./lightswind/sparkle-particles";
import { useState } from "react";
import { Box, Button, Paper, TextField, Typography } from "@mui/material";
import { ParticlesProvider } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import myBG from "../BuildSync BG.png";
import myLG from "../BuildSync LG(B).png";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [hasError, setHasError] = useState(false);

  const handleSubmit = (event) => {
    event.preventDefault();

    if (username === "admin" && password === "admin") {
      onLogin();
      return;
    }

    setHasError(true);
  };

  return (
    <ParticlesProvider init={async (engine) => { await loadSlim(engine); }}>
    <Box
      sx={{
        minHeight: "100vh",
        position: "relative",
        isolation: "isolate",
        overflow: "hidden",
        display: "grid",
        placeItems: "center",
        p: 2,
        backgroundImage: `url("${myBG}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      <SparkleParticles
        className="login-particles"
        maxParticleSize={1.5}
        minParticleSize={0.5}
        baseDensity={600}
        maxSpeed={2}
        minMoveSpeed={0.1}
        maxOpacity={0.8}
        customDirection="none"
        opacityAnimationSpeed={7}
        minParticleOpacity={0.1}
        particleColor="#ffa200"
        enableParallax={true}
        enableHoverGrab={true}
        backgroundColor="transparent"
        zIndexLevel={0}
        clickEffect={true}
        hoverMode="bubble"
        particleCount={3}
        particleShape="circle"
        enableCollisions={true}
      />
      <Paper
        elevation={8}
        sx={{
          width: "min(100%, 420px)",
          p: { xs: 3, sm: 5 },
          borderRadius: 2,
          color: "black",
          position: "relative",
          zIndex: 10,
        }}
      >
        <Box component="form" onSubmit={handleSubmit}>
          <Box
            component="img"
            src={myLG}
            alt="BuildSync"
            sx={{ display: "block", width: "min(100%, 220px)", height: 50, objectFit: "contain", mb: 3 }}
          />
          <Typography component="h1" variant="h5" fontWeight={700} mb={0.5}>
            Sign in
          </Typography>
          <Typography color="#000000" mb={0} fontSize="0.875rem">
            Please enter your credentials to access your account.
          </Typography>
          <TextField
            label="Username"
            value={username}
            onChange={(event) => {
              setUsername(event.target.value);
              setHasError(false);
            }}
            autoComplete="username"
            required
            fullWidth
            margin="normal"
            sx={{
                "& .MuiInputBase-input": {
                color: "black",
                },
            }}
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              setHasError(false);
            }}
            autoComplete="current-password"
            required
            fullWidth
            margin="normal"
            sx={{
                "& .MuiInputBase-input": {
                color: "black",
                },
            }}
            error={hasError}
            helperText={hasError ? "Invalid username or password." : " "}
          />
          <Button type="submit" variant="contained" fullWidth size="large" sx={{ mt: 1 }}>
            Sign in
          </Button>
        </Box>
      </Paper>
    </Box>
    </ParticlesProvider>
  );
}