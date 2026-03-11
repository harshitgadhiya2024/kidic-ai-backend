# CI/CD Setup Guide — Kidic AI Backend

**Stack:** GitHub Actions → AWS EC2 → Python (no Docker) → systemd

Every push to `main` automatically deploys to your EC2 instance.

---

## Overview

```
Push to main
     │
     ▼
GitHub Actions
     │  SSH into EC2
     ▼
EC2 Instance
  ├── git pull origin main
  ├── pip install -r requirements.txt
  └── sudo systemctl restart kidic-ai
```

---

## Part 1 — EC2 Instance Setup (run once)

SSH into your EC2 instance first:

```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 1.1 Update system & install Python 3.11

Ubuntu's default repos may not include Python 3.11. Add the `deadsnakes` PPA first:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev git
```

Verify:

```bash
python3.11 --version
```

### 1.2 Clone the repository

```bash
cd ~
git clone https://github.com/harshitgadhiya2024/kidic-ai-backend.git kidic-ai
cd kidic-ai
```

### 1.3 Create a virtual environment and install dependencies

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 1.4 Create the `.env` file

```bash
nano .env
```

Paste your full `.env` contents and save (`Ctrl+X → Y → Enter`).

### 1.5 Test the app runs manually

```bash
source venv/bin/activate
python main.py
```

Visit `http://<EC2_PUBLIC_IP>:8020/health` — you should see `{"status": "healthy"}`.

Press `Ctrl+C` to stop.

---

## Part 2 — systemd Service (keeps app running forever)

### 2.1 Create the service file

```bash
sudo nano /etc/systemd/system/kidic-ai.service
```

Paste the following (replace `ubuntu` with your actual EC2 username if different):

```ini
[Unit]
Description=Kidic AI FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/kidic-ai
ExecStart=/home/ubuntu/kidic-ai/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8020 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Save and exit (`Ctrl+X → Y → Enter`).

### 2.2 Enable and start the service

```bash
sudo systemctl daemon-reload
sudo systemctl enable kidic-ai
sudo systemctl start kidic-ai
```

### 2.3 Check service status

```bash
sudo systemctl status kidic-ai
```

You should see `Active: active (running)`.

### 2.4 Allow passwordless restart for GitHub Actions

The deploy script runs `sudo systemctl restart kidic-ai` over SSH. To allow this without a password:

```bash
sudo visudo
```

Add this line at the bottom (replace `ubuntu` with your EC2 username):

```
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart kidic-ai
```

Save and exit.

---

## Part 3 — AWS Security Group

In the AWS Console:

1. Go to **EC2 → Instances → your instance**
2. Click the **Security Group** link
3. Click **Edit inbound rules → Add rule**
4. Add:

| Type | Protocol | Port | Source |
|------|----------|------|--------|
| Custom TCP | TCP | 8020 | 0.0.0.0/0 |
| SSH | TCP | 22 | Your IP (or 0.0.0.0/0) |

5. Click **Save rules**

---

## Part 4 — GitHub Secrets

Go to your GitHub repo:  
**Settings → Secrets and variables → Actions → New repository secret**

Add these 4 secrets:

| Secret Name | Value | How to get it |
|-------------|-------|---------------|
| `EC2_HOST` | Your EC2 public IP | AWS Console → EC2 → Public IPv4 address |
| `EC2_USER` | `ubuntu` | Default for Ubuntu AMI (or `ec2-user` for Amazon Linux) |
| `EC2_SSH_KEY` | Full contents of your `.pem` file | `cat ~/Downloads/your-key.pem` |
| `ENV_FILE` | Full contents of your `.env` file | Copy from your local `.env` |

### Getting your SSH key content:

```bash
cat ~/Downloads/your-key.pem
```

Copy everything including `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----`.

---

## Part 5 — How Deployment Works

Once everything is set up, every push to `main`:

1. GitHub Actions triggers automatically
2. SSHs into your EC2 using the stored key
3. Runs `git pull origin main` to get latest code
4. Writes the `.env` file from the `ENV_FILE` secret
5. Activates the virtualenv and runs `pip install -r requirements.txt`
6. Runs `sudo systemctl restart kidic-ai` to restart the app

**Total deploy time: ~30–60 seconds**

---

## Useful Commands on EC2

```bash
# View live logs
sudo journalctl -u kidic-ai -f

# View last 100 lines of logs
sudo journalctl -u kidic-ai -n 100

# Restart the app manually
sudo systemctl restart kidic-ai

# Stop the app
sudo systemctl stop kidic-ai

# Check app status
sudo systemctl status kidic-ai
```

---

## Verify Deployment

After a push to `main`, check:

1. **GitHub Actions tab** in your repo — the workflow should show a green checkmark
2. **API health check:**

```bash
curl http://<EC2_PUBLIC_IP>:8020/health
```

Expected response:
```json
{"status": "healthy", "service": "Kidic AI API"}
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Unable to locate package python3.11` | Run `sudo add-apt-repository ppa:deadsnakes/ppa -y && sudo apt update` then retry install |
| Workflow fails at SSH step | Check `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` secrets are correct |
| App not starting | Run `sudo journalctl -u kidic-ai -n 50` on EC2 to see errors |
| Port 8020 not accessible | Check EC2 Security Group inbound rules |
| `sudo systemctl restart` fails | Make sure the `visudo` passwordless entry is added (Part 2.4) |
| `pip install` fails | SSH into EC2 and run manually to see the error |
| `.env` missing variables | Update the `ENV_FILE` GitHub secret with the latest `.env` content |
