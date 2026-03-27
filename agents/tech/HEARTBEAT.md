# HEARTBEAT.md

# Check devops agent status every 5 minutes
- cron: "*/5 * * * *"
  task: "Check if devops services are running and healthy"
  tool: "exec"
  args: ["systemctl status devops-agent --no-pager"]
