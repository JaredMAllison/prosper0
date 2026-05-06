# Desktop GPU Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Ariel von Prosper0 from Gretchen to the Windows 11 desktop (RTX 3070, 10.0.0.78), running persistently inside WSL2 with GPU-accelerated Ollama, vault read from Gretchen, and a single `ariel` shell alias that brings everything up and opens the web console.

**Architecture:** Docker Engine inside WSL2 (not Docker Desktop) with systemd enabled, so services survive without a Windows login. The NVIDIA Container Toolkit passes the RTX 3070 through to the Ollama container. The prosper0 repo lives in the WSL2 native filesystem (not `/mnt/c/`). Vault is rsync'd read-only from Gretchen on a 5-minute timer.

**Tech Stack:** WSL2 Ubuntu, systemd, Docker Engine CE, NVIDIA Container Toolkit, git, rsync, `xdg-open` / PowerShell for browser launch.

---

## Prerequisites

- Desktop IP: `10.0.0.78` (Windows 11, RTX 3070 8GB VRAM)
- Gretchen IP: `10.0.0.8` (vault source, SSH key already set up)
- WSL2 installed with Ubuntu, currently stopped (`wsl --install` done)
- Claude Code running inside WSL2 Ubuntu on the desktop

All commands below run **inside the WSL2 terminal** unless noted as `[Windows]`.

---

## File Map

| Action | Path |
|---|---|
| Create | `/etc/wsl.conf` — enable systemd |
| Create | `~/.config/systemd/user/prosper0.service` — docker-compose auto-start |
| Create | `~/.config/systemd/user/vault-sync.service` — rsync one-shot |
| Create | `~/.config/systemd/user/vault-sync.timer` — 5-min rsync timer |
| Modify | `~/prosper0/deploy/docker-compose.yml` — add GPU device reservation |
| Create | `~/prosper0/deploy/.env` — local env overrides (vault path, model) |
| Create | `~/.local/bin/ariel` — shell script that starts stack + opens browser |
| Modify | `~/.bashrc` — add `~/.local/bin` to PATH |

---

### Task 1: Enable systemd in WSL2

**Files:**
- Create: `/etc/wsl.conf`

- [ ] **Step 1: Write the wsl.conf file**

  ```bash
  sudo tee /etc/wsl.conf > /dev/null << 'EOF'
  [boot]
  systemd=true
  EOF
  ```

- [ ] **Step 2: Verify the file**

  ```bash
  cat /etc/wsl.conf
  ```

  Expected:
  ```
  [boot]
  systemd=true
  ```

- [ ] **Step 3: Shut down WSL2 from Windows to apply**

  `[Windows PowerShell]`:
  ```powershell
  wsl --shutdown
  ```

  Then reopen the Ubuntu terminal. Wait ~10 seconds for WSL2 to restart.

- [ ] **Step 4: Verify systemd is running**

  ```bash
  systemctl --user status
  ```

  Expected: output includes `State: running` — not `degraded` or `failed`.

---

### Task 2: Install Docker Engine inside WSL2

**Files:** No project files. System packages only.

- [ ] **Step 1: Remove any conflicting packages**

  ```bash
  for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    sudo apt-get remove -y $pkg 2>/dev/null || true
  done
  ```

- [ ] **Step 2: Add Docker's apt repository**

  ```bash
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  ```

- [ ] **Step 3: Install Docker Engine**

  ```bash
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  ```

- [ ] **Step 4: Add your user to the docker group**

  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

- [ ] **Step 5: Enable and start Docker via systemd**

  ```bash
  sudo systemctl enable docker
  sudo systemctl start docker
  ```

- [ ] **Step 6: Verify Docker is running**

  ```bash
  docker run --rm hello-world
  ```

  Expected: `Hello from Docker!` message.

---

### Task 3: Install NVIDIA Container Toolkit

**Files:** No project files. System packages only.

- [ ] **Step 1: Add NVIDIA Container Toolkit apt repository**

  ```bash
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  ```

- [ ] **Step 2: Install the toolkit**

  ```bash
  sudo apt-get update
  sudo apt-get install -y nvidia-container-toolkit
  ```

- [ ] **Step 3: Configure Docker to use the NVIDIA runtime**

  ```bash
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  ```

- [ ] **Step 4: Verify GPU passthrough**

  ```bash
  docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu20.04 nvidia-smi
  ```

  Expected: `nvidia-smi` output showing the RTX 3070 with driver version and CUDA version.

  > If this fails with "unknown flag: --gpus", Docker didn't pick up the nvidia runtime. Check `/etc/docker/daemon.json` — it should contain `"runtimes": {"nvidia": {...}}`.

---

### Task 4: Clone prosper0 repo from Gretchen

**Files:**
- Create: `~/prosper0/` (cloned repo)

- [ ] **Step 1: Verify SSH access to Gretchen**

  ```bash
  ssh jared@10.0.0.8 "hostname && echo OK"
  ```

  Expected: `TPC-2026-Jared` and `OK`.

  If this fails, the SSH key isn't set up. Run:
  ```bash
  ssh-copy-id jared@10.0.0.8
  ```

- [ ] **Step 2: Clone the repo**

  ```bash
  cd ~
  git clone jared@10.0.0.8:~/prosper0 prosper0
  ```

  Expected: repo clones to `~/prosper0/` with all branches.

- [ ] **Step 3: Verify the clone**

  ```bash
  ls ~/prosper0/stack/api/server.py ~/prosper0/console/index.html
  ```

  Both paths must exist.

---

### Task 5: Add GPU config to docker-compose

The Ollama service needs explicit GPU resource reservation to use the RTX 3070. Docker Compose requires the `deploy` key with `nvidia` device capabilities.

**Files:**
- Modify: `~/prosper0/deploy/docker-compose.yml`
- Create: `~/prosper0/deploy/.env`

- [ ] **Step 1: Add GPU reservation to the ollama service**

  In `~/prosper0/deploy/docker-compose.yml`, replace the `ollama` service block with:

  ```yaml
  ollama:
    image: ollama/ollama:latest
    container_name: prosper0-ollama
    volumes:
      - ${OLLAMA_MODELS_PATH:-./models}:/root/.ollama
    ports:
      - "11434:11434"
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "ollama", "list"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
  ```

- [ ] **Step 2: Create the local .env file**

  ```bash
  cat > ~/prosper0/deploy/.env << 'EOF'
  VAULT_PATH=/home/jared/vault
  OLLAMA_MODELS_PATH=/home/jared/ollama-models
  AUDIT_LOG_PATH=/home/jared/prosper0-logs
  OLLAMA_MODEL=qwen2.5:7b
  EOF
  ```

  The vault path (`/home/jared/vault`) is where rsync will write the synced vault (Task 6). The models path keeps Ollama model weights outside the repo.

- [ ] **Step 3: Create the required directories**

  ```bash
  mkdir -p ~/vault ~/ollama-models ~/prosper0-logs
  ```

- [ ] **Step 4: Commit the docker-compose change**

  ```bash
  cd ~/prosper0
  git checkout -b feat/desktop-gpu-setup
  git add deploy/docker-compose.yml
  git commit -m "feat: add GPU device reservation for RTX 3070 in ollama service"
  ```

  Note: `.env` is gitignored — do not add it.

---

### Task 6: Set up vault rsync from Gretchen

The vault at `/home/jared/Documents/Obsidian/Marlin` on Gretchen is rsync'd read-only to `~/vault` on the desktop every 5 minutes. Ariel reads it; it never writes back.

**Files:**
- Create: `~/.config/systemd/user/vault-sync.service`
- Create: `~/.config/systemd/user/vault-sync.timer`

- [ ] **Step 1: Create the rsync service unit**

  ```bash
  mkdir -p ~/.config/systemd/user
  cat > ~/.config/systemd/user/vault-sync.service << 'EOF'
  [Unit]
  Description=Sync Marlin vault from Gretchen
  After=network-online.target

  [Service]
  Type=oneshot
  ExecStart=rsync -az --delete jared@10.0.0.8:/home/jared/Documents/Obsidian/Marlin/ /home/jared/vault/
  EOF
  ```

- [ ] **Step 2: Create the timer unit**

  ```bash
  cat > ~/.config/systemd/user/vault-sync.timer << 'EOF'
  [Unit]
  Description=Sync Marlin vault every 5 minutes

  [Timer]
  OnBootSec=30
  OnUnitActiveSec=5min
  Unit=vault-sync.service

  [Install]
  WantedBy=timers.target
  EOF
  ```

- [ ] **Step 3: Enable and start the timer**

  ```bash
  systemctl --user daemon-reload
  systemctl --user enable --now vault-sync.timer
  ```

- [ ] **Step 4: Trigger a manual sync and verify**

  ```bash
  systemctl --user start vault-sync.service
  systemctl --user status vault-sync.service
  ls ~/vault/Tasks/ | head -5
  ```

  Expected: vault-sync.service shows `status=0/SUCCESS`; Tasks/ has `.md` files.

---

### Task 7: Pull and start Ollama with GPU, pull model

Ollama model weights need to be pulled before Ariel can answer. Qwen2.5:7b Q5_K_M is ~5.8GB and fits the RTX 3070's 8GB VRAM.

- [ ] **Step 1: Start the docker-compose stack**

  ```bash
  cd ~/prosper0/deploy
  docker compose up -d
  ```

- [ ] **Step 2: Verify Ollama is running with GPU**

  ```bash
  docker logs prosper0-ollama | tail -20
  ```

  Expected: logs show CUDA initialization, no errors.

  ```bash
  docker exec prosper0-ollama nvidia-smi
  ```

  Expected: nvidia-smi shows RTX 3070 from inside the container.

- [ ] **Step 3: Pull the model**

  ```bash
  docker exec prosper0-ollama ollama pull qwen2.5:7b
  ```

  This downloads ~5.8GB. Wait for completion.

- [ ] **Step 4: Verify the model loads on GPU**

  ```bash
  docker exec prosper0-ollama ollama run qwen2.5:7b "say 'GPU confirmed' and nothing else"
  ```

  Expected: response `GPU confirmed`. Check `nvidia-smi` on host in another terminal — VRAM usage should spike to ~6GB while the model is running.

---

### Task 8: Create systemd service for docker-compose auto-start

This makes the Ariel stack start automatically when WSL2 boots (which happens automatically at Windows boot once Task 9 is done).

**Files:**
- Create: `~/.config/systemd/user/prosper0.service`

- [ ] **Step 1: Create the service unit**

  ```bash
  cat > ~/.config/systemd/user/prosper0.service << 'EOF'
  [Unit]
  Description=Prosper0 (Ariel) AI stack
  After=docker.service network-online.target
  Requires=docker.service

  [Service]
  Type=exec
  WorkingDirectory=/home/jared/prosper0/deploy
  ExecStart=docker compose up
  ExecStop=docker compose down
  Restart=on-failure
  RestartSec=10

  [Install]
  WantedBy=default.target
  EOF
  ```

- [ ] **Step 2: Enable the service (but don't start it yet — GPU verify first)**

  ```bash
  systemctl --user daemon-reload
  systemctl --user enable prosper0.service
  ```

- [ ] **Step 3: Verify it would start cleanly**

  Stop the compose stack if running, then let systemd start it:

  ```bash
  cd ~/prosper0/deploy && docker compose down
  systemctl --user start prosper0.service
  sleep 15
  systemctl --user status prosper0.service
  curl -s http://localhost:8080/v1/health | python3 -m json.tool
  ```

  Expected: service active, health endpoint returns layer statuses.

---

### Task 9: Configure WSL2 to auto-start at Windows boot

WSL2 normally only runs when a terminal is open. This Task Scheduler entry starts WSL2 silently at boot, which triggers systemd, which starts prosper0.service and vault-sync.timer — before anyone logs in.

`[Windows PowerShell — run as Administrator]`

- [ ] **Step 1: Create the Task Scheduler entry**

  ```powershell
  $action = New-ScheduledTaskAction -Execute "wsl.exe" -Argument "-d Ubuntu"
  $trigger = New-ScheduledTaskTrigger -AtStartup
  $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0
  $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
  Register-ScheduledTask -TaskName "WSL2 Autostart" -Action $action -Trigger $trigger -Settings $settings -Principal $principal
  ```

- [ ] **Step 2: Verify the task was created**

  ```powershell
  Get-ScheduledTask -TaskName "WSL2 Autostart" | Select-Object TaskName, State
  ```

  Expected: `TaskName: WSL2 Autostart`, `State: Ready`.

- [ ] **Step 3: Test by simulating a reboot**

  Shut down WSL2 from PowerShell:
  ```powershell
  wsl --shutdown
  ```

  Wait 30 seconds, then from a Windows terminal:
  ```powershell
  wsl -d Ubuntu -- curl -s http://localhost:8080/v1/health
  ```

  Expected: JSON health response — Ariel is up without you launching a WSL2 terminal.

---

### Task 10: Create the `ariel` alias

The `ariel` command does two things: ensures the stack is running, then opens the web console in the default browser.

From WSL2, opening a Windows browser requires calling `cmd.exe /c start` or PowerShell. The `wslview` utility (from `wslu`) handles this cleanly.

**Files:**
- Create: `~/.local/bin/ariel`
- Modify: `~/.bashrc` (PATH addition)

- [ ] **Step 1: Install wslu (provides wslview)**

  ```bash
  sudo apt-get install -y wslu
  ```

- [ ] **Step 2: Create the ariel script**

  ```bash
  mkdir -p ~/.local/bin
  cat > ~/.local/bin/ariel << 'EOF'
  #!/usr/bin/env bash
  set -e

  CONSOLE_URL="http://localhost:8080"

  # Ensure prosper0 stack is running
  if ! systemctl --user is-active --quiet prosper0.service; then
    echo "Starting Ariel..."
    systemctl --user start prosper0.service
    echo -n "Waiting for API"
    for i in $(seq 1 30); do
      if curl -sf "$CONSOLE_URL/v1/health" > /dev/null 2>&1; then
        echo " ready."
        break
      fi
      echo -n "."
      sleep 2
    done
  else
    echo "Ariel is running."
  fi

  # Open web console in Windows default browser
  wslview "$CONSOLE_URL"
  EOF
  chmod +x ~/.local/bin/ariel
  ```

- [ ] **Step 3: Add ~/.local/bin to PATH in .bashrc**

  ```bash
  grep -q 'local/bin' ~/.bashrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  ```

- [ ] **Step 4: Test the alias**

  ```bash
  ariel
  ```

  Expected:
  - If stack is already running: `Ariel is running.` then browser opens to console.
  - If stack is stopped: `Starting Ariel...` then dots while it comes up, then browser opens.

---

## Verification Checklist

After all tasks complete:

- [ ] `nvidia-smi` inside the Ollama container shows the RTX 3070
- [ ] `ollama run qwen2.5:7b "ping"` responds from GPU (VRAM spikes in `nvidia-smi`)
- [ ] `curl http://localhost:8080/v1/health` returns all layers
- [ ] `ls ~/vault/Tasks/` has current Marlin tasks (rsync works)
- [ ] After `wsl --shutdown` + 30s, `curl http://localhost:8080/v1/health` works without opening WSL2 terminal
- [ ] `ariel` opens the console and starts the stack if stopped
- [ ] Web console at `http://10.0.0.78:8080` is reachable from Gretchen or any LAN device

---

## Notes

- **Model VRAM**: Qwen2.5:7b Q5_K_M uses ~5.8GB. RTX 3070 has 8GB. Leave headroom — don't run other GPU workloads simultaneously.
- **Vault is read-only on desktop**: The rsync is one-way Gretchen→desktop. Do not write vault files on the desktop — they'll be overwritten on the next sync.
- **Gretchen stays as fallback**: Don't shut down Gretchen's prosper0 stack until the desktop is confirmed stable for a full work session.
- **`.env` is not committed**: Local paths (vault location, model path) live in `deploy/.env` which is gitignored.
