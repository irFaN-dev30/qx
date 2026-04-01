# ===================================================================
# Final and Corrected .idx/dev.nix for Project QX
# Author: Gemini (with apologies for previous errors)
# This version uses a simplified, standard, and robust structure.
# ===================================================================
{ pkgs, ... }: {
  # Use a stable Nix channel
  channel = "stable-24.05";

  # Define the necessary system packages.
  # Nix lists are space-separated. No commas.
  packages = [
    pkgs.python311
    pkgs.nodejs_20
    pkgs.python311Packages.pip
    pkgs.python311Packages.playwright
    pkgs.git
  ];

  # IDX specific configurations
  idx = {
    # Recommended extensions for your project
    extensions = [
      "ms-python.python"
      "esbenp.prettier-vscode"
    ];

    # Workspace lifecycle hooks for automation
    workspace = {
      # Commands that run ONCE when the workspace is first created.
      # Each command is a separate, simple attribute for reliability.
      onCreate = {
        install-npm-deps = "cd dashboard && npm install";
        install-pip-deps = "pip install -r functions/signal_function/requirements.txt";
        install-playwright-browsers = "playwright install --with-deps";
      };

      # Commands that run EVERY time the workspace starts.
      onStart = {
        check-playwright = "playwright install --with-deps";
      };
    };

    # Configuration for the web preview panel.
    previews = {
      enable = true;
      previews = {
        web = {
          # Command to start the Next.js development server.
          command = [ "npm" "run" "dev" ];
          # Run this command inside the 'dashboard' directory.
          cwd = "dashboard";
          manager = "web";
        };
      };
    };
  };

  # Environment variables can be set here.
  env = {};
}
