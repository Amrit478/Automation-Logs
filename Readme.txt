Your monitoring stack is located at **`/opt/monitoring/`** on your Ubuntu host.

To combine your **Docker Monitoring Stack** and your **Automation Scripts** (`Automation-Logs`) into a single GitHub repository, structure your files in a unified directory.

---

### Target Folder Structure

Organize the repository layout so Docker configs and Python/Jinja automation scripts live in clean, separate folders:

```text
Automation-Logs/               <-- Root Git Repository
│
├── automation/                <-- Netmiko & Jinja Automation
│   ├── vars.yml
│   ├── cisco_logging.j2
│   ├── deploy_configs.py
│   └── output/                <-- Generated .cfg files (ignored by git)
│
├── monitoring/                <-- Docker Stack Configs (/opt/monitoring)
│   ├── docker-compose.yml
│   ├── config.alloy
│   ├── prometheus.yml
│   ├── blackbox.yml
│   └── targets/
│       ├── cisco.yml
│       ├── icmp.yml
│       └── tcp.yml
│
├── .gitignore
└── README.md

```

---

### How to Merge Your Local Host Stack into GitHub

Run these commands on your **Ubuntu host terminal** to copy your live `/opt/monitoring` configuration files into your local Git repository folder and push them to GitHub:

```bash
# 1. Navigate to your git repository directory
cd ~/Automation-Logs   # (or wherever your repo is cloned)

# 2. Pull latest changes from master
git pull origin master

# 3. Create folders for clean organization
mkdir -p automation monitoring

# 4. Move your automation files into the automation/ directory
mv vars.yml cisco_logging.j2 deploy_configs.py automation/ 2>/dev/null || true

# 5. Copy the live monitoring stack files from /opt/monitoring/
cp -r /opt/monitoring/* monitoring/

# 6. Create a .gitignore file to ignore temporary logs/outputs
cat << 'EOF' > .gitignore
automation/output/
*.pyc
__pycache__/
.DS_Store
EOF

# 7. Add, commit, and push everything to GitHub
git add .
git commit -m "Add Docker monitoring stack from /opt/monitoring and structure repo"
git push origin master

```

---

### Deploying & Managing Services from the Repository

Once structured this way:

1. **To run or update your Docker Monitoring Stack**:
```bash
cd ~/Automation-Logs/monitoring
sudo docker compose up -d

```


2. **To deploy NetFlow/Syslog configs to Cisco devices**:
```bash
cd ~/Automation-Logs/automation
python3 deploy_configs.py

```
