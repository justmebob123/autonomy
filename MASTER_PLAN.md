# MASTER PLAN: Autonomous System Administration Suite (ASAS)

> **⚠️ READ-ONLY FOR AI PIPELINE**  
> This document defines the complete specification for the system administration suite.
> The AI pipeline reads this file but NEVER modifies it.
> Human maintainers update this document to change project direction.

---

## Project Vision

Build a comprehensive, production-ready Linux system administration tool that provides:
- **Proactive Monitoring**: Detect issues before they become critical
- **Automated Response**: Take corrective action when safe to do so
- **Intelligent Alerting**: Notify administrators through multiple channels
- **Historical Analysis**: Track trends and predict future issues
- **Security Hardening**: Monitor for threats and enforce security policies

The tool must be lightweight, efficient (suitable for CPU-only systems), and work across
RHEL/CentOS, Ubuntu/Debian, and other major Linux distributions.

---

## Primary Objectives

### 1. System Health Monitoring
- Monitor CPU, memory, swap, and load average
- Track process counts and zombie processes
- Monitor system uptime and recent reboots
- Detect runaway processes consuming excessive resources

### 2. Disk and Storage Management
- Monitor disk usage on all mounted filesystems
- Track inode usage (often overlooked cause of "disk full" issues)
- Monitor disk I/O performance and latency
- Integrate with SMART for disk health prediction
- Alert on approaching capacity thresholds (warning: 80%, critical: 90%)
- Identify large files and directories consuming space
- Track disk usage trends over time

### 3. Service and Process Monitoring
- Monitor systemd service status
- Detect failed and crashed services
- Optional auto-restart of critical services
- Track service resource consumption
- Monitor critical processes (sshd, cron, etc.)
- Detect services listening on unexpected ports

### 4. Security Monitoring
- Parse /var/log/auth.log and /var/log/secure for authentication events
- Detect SSH brute force attacks (multiple failed logins)
- Monitor sudo usage and privilege escalation
- Track user login/logout events
- Detect new user account creation
- Monitor changes to critical system files (/etc/passwd, /etc/shadow, /etc/sudoers)
- Check for unauthorized SUID/SGID binaries
- Monitor open ports and network connections

### 5. Log Analysis
- Parse syslog, journald, and application logs
- Pattern matching for errors, warnings, and critical events
- Configurable regex patterns for custom log parsing
- Log rotation monitoring
- Aggregate and summarize log events
- Detect log anomalies (sudden spike in errors)

### 6. Firewall Monitoring
- Monitor iptables/nftables/firewalld status
- Detect rule changes
- Backup current firewall rules
- Alert on firewall being disabled
- Track blocked connection attempts

### 7. Hardware Health
- SMART disk monitoring for HDD/SSD health
- CPU temperature monitoring (where available)
- Memory error detection via dmesg/mcelog
- RAID array status monitoring (mdadm, hardware RAID)
- Network interface status and error counters
- Power supply and UPS status (where available)

### 8. Network Monitoring
- Monitor network interface status (up/down)
- Track bandwidth usage per interface
- Detect network errors and dropped packets
- Monitor DNS resolution
- Check connectivity to critical endpoints
- Track established connections and connection states

### 9. Alerting System
- Email notifications via SMTP
- Webhook notifications (Slack, Discord, Teams, custom)
- Local logging of all alerts
- Alert aggregation (don't spam on repeated issues)
- Alert escalation (warning → critical)
- Configurable alert thresholds per check
- Quiet hours / maintenance windows

### 10. Reporting and History
- Store historical metrics in SQLite database
- Generate daily/weekly summary reports
- Trend analysis for capacity planning
- Export data in JSON/CSV formats
- Optional web dashboard for visualization

---

## Architecture

```
asas/
├── main.py                     # Entry point, CLI interface
├── asas.py                     # Main application class
├── config/
│   ├── __init__.py
│   ├── settings.yaml           # Main configuration
│   ├── alerts.yaml             # Alert channel configuration
│   └── checks.yaml             # Check-specific configuration
├── core/
│   ├── __init__.py
│   ├── config.py               # Configuration loader with validation
│   ├── logger.py               # Centralized logging setup
│   ├── scheduler.py            # APScheduler-based task scheduler
│   ├── database.py             # SQLite database for history
│   └── utils.py                # Shared utility functions
├── monitors/
│   ├── __init__.py
│   ├── base.py                 # Base monitor class (abstract)
│   ├── system.py               # CPU, memory, load monitoring
│   ├── disk.py                 # Disk usage and I/O monitoring
│   ├── services.py             # Systemd service monitoring
│   ├── security.py             # Security and auth monitoring
│   ├── logs.py                 # Log file analysis
│   ├── firewall.py             # Firewall status monitoring
│   ├── hardware.py             # Hardware health (SMART, temps)
│   └── network.py              # Network interface monitoring
├── alerts/
│   ├── __init__.py
│   ├── base.py                 # Base alert handler class
│   ├── manager.py              # Alert aggregation and dispatch
│   ├── email.py                # Email notifications
│   ├── webhook.py              # Webhook notifications
│   └── local.py                # Local file logging of alerts
├── reports/
│   ├── __init__.py
│   ├── generator.py            # Report generation
│   └── templates/              # Report templates
├── cli/
│   ├── __init__.py
│   └── commands.py             # CLI command definitions
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── test_monitors/          # Monitor unit tests
│   ├── test_alerts/            # Alert handler tests
│   └── test_integration/       # Integration tests
├── docs/
│   ├── installation.md
│   ├── configuration.md
│   └── monitors.md
├── scripts/
│   ├── install.sh              # Installation script
│   └── asas.service            # Systemd service file
├── requirements.txt
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## Component Specifications

### Core Components

#### config.py - Configuration Loader
```python
# Must implement:
- load_config(path: str) -> Config
- validate_config(config: dict) -> bool
- merge_configs(base: dict, override: dict) -> dict
- get_env_overrides() -> dict  # Support ENV variable overrides
- Config dataclass with typed fields
```

#### logger.py - Logging Setup
```python
# Must implement:
- setup_logging(config: LogConfig) -> logging.Logger
- Support for: console, file, syslog outputs
- Log rotation (size-based and time-based)
- Structured logging with JSON option
- Context managers for operation timing
```

#### scheduler.py - Task Scheduler
```python
# Must implement:
- Scheduler class wrapping APScheduler
- add_monitor(monitor: BaseMonitor, interval: int)
- remove_monitor(name: str)
- pause() / resume()
- get_status() -> dict
- Graceful shutdown handling
```

#### database.py - History Storage
```python
# Must implement:
- Database class for SQLite operations
- store_metric(monitor: str, metric: str, value: float, timestamp: datetime)
- get_metrics(monitor: str, metric: str, start: datetime, end: datetime) -> List
- cleanup_old_data(retention_days: int)
- Schema migration support
```

### Monitor Base Class

#### base.py - Abstract Base Monitor
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class Severity(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class CheckResult:
    name: str
    severity: Severity
    message: str
    value: Optional[float] = None
    details: Optional[dict] = None
    timestamp: datetime = field(default_factory=datetime.now)

class BaseMonitor(ABC):
    """Abstract base class for all monitors."""
    
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.enabled = config.get('enabled', True)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this monitor."""
        pass
    
    @abstractmethod
    async def check(self) -> List[CheckResult]:
        """Perform monitoring check and return results."""
        pass
    
    def get_thresholds(self, check_name: str) -> dict:
        """Get warning/critical thresholds for a check."""
        pass
```

### Monitor Implementations

#### system.py - System Monitor
```python
# Checks to implement:
- cpu_usage: Overall CPU utilization percentage
- cpu_per_core: Per-core utilization
- memory_usage: RAM utilization percentage
- swap_usage: Swap utilization percentage
- load_average: 1, 5, 15 minute load averages
- process_count: Total process count
- zombie_processes: Zombie process detection
- uptime: System uptime
- runaway_processes: Processes using >X% CPU for >Y minutes
```

#### disk.py - Disk Monitor
```python
# Checks to implement:
- disk_usage: Per-filesystem usage percentage
- inode_usage: Per-filesystem inode usage
- disk_io: Read/write throughput and IOPS
- disk_latency: I/O latency
- large_files: Files over configurable size
- disk_growth: Usage trend analysis
```

#### services.py - Service Monitor
```python
# Checks to implement:
- service_status: Check if services are running
- service_failed: Detect failed services
- service_resources: CPU/memory per service
- auto_restart: Optionally restart failed services
- critical_processes: Check specific process names
```

#### security.py - Security Monitor
```python
# Checks to implement:
- failed_logins: Failed SSH/login attempts
- brute_force: Multiple failures from same IP
- sudo_usage: Sudo command execution
- user_changes: New users, password changes
- file_integrity: Changes to critical files
- suid_binaries: Unauthorized SUID/SGID files
- open_ports: Unexpected listening ports
- ssh_sessions: Active SSH connections
```

#### logs.py - Log Monitor
```python
# Checks to implement:
- error_patterns: Configurable regex matching
- log_rate: Detect abnormal log rates
- specific_messages: Watch for specific strings
- log_rotation: Verify logs are rotating
```

#### firewall.py - Firewall Monitor
```python
# Checks to implement:
- firewall_status: Is firewall active?
- rule_changes: Detect rule modifications
- blocked_attempts: Count blocked connections
- rule_backup: Backup current rules
```

#### hardware.py - Hardware Monitor
```python
# Checks to implement:
- smart_status: Disk SMART health
- cpu_temperature: CPU temp (requires lm-sensors)
- memory_errors: ECC/memory errors
- raid_status: mdadm array status
- dmesg_errors: Hardware errors in dmesg
```

#### network.py - Network Monitor
```python
# Checks to implement:
- interface_status: Up/down state
- bandwidth_usage: RX/TX rates
- network_errors: Errors, drops, overruns
- dns_resolution: DNS health check
- connectivity: Ping critical hosts
- connections: Connection counts by state
```

### Alert System

#### manager.py - Alert Manager
```python
# Must implement:
- AlertManager class
- dispatch(result: CheckResult)
- aggregate_alerts(window: int) -> List[Alert]
- is_in_quiet_hours() -> bool
- should_escalate(alert: Alert) -> bool
- record_alert(alert: Alert)
```

#### email.py - Email Alerts
```python
# Must implement:
- EmailHandler(AlertHandler)
- send(alert: Alert) -> bool
- Support: SMTP, SMTP+TLS, SMTP+SSL
- HTML and plain text templates
- Configurable recipients per severity
```

#### webhook.py - Webhook Alerts
```python
# Must implement:
- WebhookHandler(AlertHandler)
- send(alert: Alert) -> bool
- Support: Generic webhook, Slack, Discord, Teams
- Configurable payload templates
- Retry logic with backoff
```

---

## Configuration Schema

### settings.yaml
```yaml
# Global settings
global:
  hostname: "{{ ansible_hostname }}"  # Auto-detect if not set
  check_interval: 60                   # Default interval in seconds
  history_retention_days: 30
  log_level: INFO
  log_file: /var/log/asas/asas.log

# Database
database:
  path: /var/lib/asas/history.db
  
# Monitor enable/disable and settings
monitors:
  system:
    enabled: true
    interval: 30
    thresholds:
      cpu_warning: 80
      cpu_critical: 95
      memory_warning: 80
      memory_critical: 95
      load_warning: 4.0
      load_critical: 8.0
      
  disk:
    enabled: true
    interval: 300
    thresholds:
      usage_warning: 80
      usage_critical: 90
      inode_warning: 80
      inode_critical: 90
    exclude_filesystems:
      - tmpfs
      - devtmpfs
    exclude_mountpoints:
      - /boot/efi
      
  services:
    enabled: true
    interval: 60
    services:
      - sshd
      - crond
      - rsyslog
    auto_restart: false
    auto_restart_services:
      - crond
      
  security:
    enabled: true
    interval: 60
    failed_login_threshold: 5
    failed_login_window: 300
    watch_files:
      - /etc/passwd
      - /etc/shadow
      - /etc/sudoers
      - /etc/ssh/sshd_config
      
  logs:
    enabled: true
    interval: 60
    patterns:
      - name: errors
        regex: "error|fail|critical"
        severity: warning
      - name: oom_killer
        regex: "Out of memory|oom-killer"
        severity: critical
    log_files:
      - /var/log/syslog
      - /var/log/messages
      
  firewall:
    enabled: true
    interval: 300
    backup_rules: true
    backup_path: /var/lib/asas/firewall_backup
    
  hardware:
    enabled: true
    interval: 3600
    smart_enabled: true
    temperature_enabled: true
    
  network:
    enabled: true
    interval: 60
    interfaces:
      - eth0
      - ens192
    ping_hosts:
      - 8.8.8.8
      - 1.1.1.1
```

### alerts.yaml
```yaml
# Alert configuration
alerts:
  # Global settings
  enabled: true
  aggregate_window: 300        # Aggregate same alerts within 5 minutes
  quiet_hours:
    enabled: false
    start: "22:00"
    end: "07:00"
    
  # Alert channels
  channels:
    email:
      enabled: true
      smtp_server: smtp.example.com
      smtp_port: 587
      smtp_tls: true
      smtp_user: alerts@example.com
      smtp_password: "${SMTP_PASSWORD}"  # From environment
      from_address: asas@example.com
      recipients:
        warning:
          - ops@example.com
        critical:
          - ops@example.com
          - oncall@example.com
          
    slack:
      enabled: false
      webhook_url: "${SLACK_WEBHOOK}"
      channel: "#alerts"
      username: "ASAS Bot"
      
    webhook:
      enabled: false
      url: "https://hooks.example.com/alerts"
      method: POST
      headers:
        Authorization: "Bearer ${WEBHOOK_TOKEN}"
```

---

## Development Rules

### Code Quality Requirements

1. **Error Handling**
   - ALL I/O operations MUST be wrapped in try/except blocks
   - NEVER let exceptions propagate to crash the main process
   - Log all exceptions with full traceback at DEBUG level
   - Return appropriate error states, don't raise exceptions from monitors

2. **Type Hints**
   - ALL functions MUST have complete type hints
   - Use `Optional[]` for nullable parameters
   - Use `List[]`, `Dict[]`, etc. from typing module
   - Define custom types for complex structures

3. **Documentation**
   - ALL modules MUST have docstrings explaining purpose
   - ALL classes MUST have docstrings with usage examples
   - ALL public functions MUST have docstrings with Args, Returns, Raises
   - Use Google-style docstring format

4. **Logging**
   - Use the logger, NEVER use print()
   - DEBUG: Detailed diagnostic information
   - INFO: Confirmation of expected operation
   - WARNING: Something unexpected but handled
   - ERROR: Failure of a specific operation
   - CRITICAL: Application cannot continue

5. **Testing**
   - Each monitor MUST have unit tests
   - Mock system calls for reproducible tests
   - Test both success and failure paths
   - Test threshold boundary conditions
   - Target: 80% code coverage minimum

### Architecture Rules

1. **Independence**: Each monitor MUST be self-contained and independently testable
2. **Configuration**: NEVER hardcode values, always use configuration
3. **Async**: Use async/await for I/O operations where appropriate
4. **Resources**: Monitors MUST clean up resources (file handles, connections)
5. **Timeouts**: ALL external calls MUST have timeouts
6. **Idempotency**: Monitors MUST be safe to run repeatedly

### Security Rules

1. NEVER log passwords, tokens, or sensitive data
2. NEVER execute shell commands with unsanitized user input
3. Run with minimum required privileges
4. Support environment variable substitution for secrets
5. Validate all configuration input

### Performance Rules

1. Monitors MUST complete within reasonable time (default: 30 seconds)
2. Minimize disk I/O and syscalls
3. Cache expensive operations where appropriate
4. Use efficient data structures
5. Profile and optimize hot paths

---

## Technology Stack

### Required Dependencies
- **Python**: 3.10+ (3.12 preferred)
- **psutil**: System and process monitoring
- **pyyaml**: Configuration parsing
- **aiofiles**: Async file operations
- **apscheduler**: Task scheduling
- **aiosqlite**: Async SQLite operations
- **jinja2**: Report templates
- **click**: CLI interface

### Optional Dependencies
- **aiosmtplib**: Async email sending
- **aiohttp**: Async HTTP for webhooks
- **smartmontools**: SMART disk monitoring (system package)
- **lm-sensors**: Temperature monitoring (system package)

### Development Dependencies
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **ruff**: Linting and formatting
- **mypy**: Type checking

---

## Quality Gates

Before any code is committed, it MUST pass:

1. **Syntax Validation**: `python -m py_compile <file>`
2. **Lint Check**: `ruff check .`
3. **Format Check**: `ruff format --check .`
4. **Type Check**: `mypy . --ignore-missing-imports`
5. **Unit Tests**: `pytest tests/ -v`
6. **Coverage**: `pytest --cov=asas --cov-fail-under=80`

---

## Development Phases

### Phase 1: Foundation (Current)
- [x] Project structure created
- [ ] Core configuration loader with validation
- [ ] Centralized logging setup
- [ ] Base monitor abstract class
- [ ] SQLite database handler
- [ ] Basic CLI structure

### Phase 2: Core Monitors
- [ ] System monitor (CPU, memory, load)
- [ ] Disk monitor (usage, inodes)
- [ ] Service monitor (systemd)
- [ ] Basic alert manager (local logging)

### Phase 3: Alerting
- [ ] Email alert handler
- [ ] Webhook alert handler
- [ ] Alert aggregation
- [ ] Alert history

### Phase 4: Security & Logs
- [ ] Security monitor
- [ ] Log monitor with patterns
- [ ] File integrity checking

### Phase 5: Advanced Monitors
- [ ] Firewall monitor
- [ ] Hardware monitor (SMART)
- [ ] Network monitor

### Phase 6: Polish
- [ ] Reporting and summaries
- [ ] Full documentation
- [ ] Installation scripts
- [ ] Systemd service file
- [ ] Package distribution

---

## Milestones

### v0.1.0 - Foundation
- [ ] Configuration system complete
- [ ] Logging system complete
- [ ] Base monitor class complete
- [ ] Database handler complete
- [ ] CLI skeleton complete

### v0.2.0 - Basic Monitoring
- [ ] System monitor complete
- [ ] Disk monitor complete
- [ ] Service monitor complete
- [ ] Local alert logging complete

### v0.3.0 - Alerting
- [ ] Email alerts complete
- [ ] Webhook alerts complete
- [ ] Alert aggregation complete

### v0.4.0 - Security
- [ ] Security monitor complete
- [ ] Log monitor complete
- [ ] File integrity checks complete

### v0.5.0 - Full Feature
- [ ] All monitors complete
- [ ] Reporting complete
- [ ] Documentation complete

### v1.0.0 - Production Ready
- [ ] Full test coverage
- [ ] Performance optimized
- [ ] Security audited
- [ ] Package published

---

## Success Criteria

The project is successful when:

1. **Reliability**: Runs continuously for 30+ days without crashes
2. **Performance**: All checks complete within timeout limits
3. **Coverage**: Detects common issues (disk full, service down, brute force)
4. **Alerting**: Successfully sends alerts through all configured channels
5. **Documentation**: New users can install and configure in < 30 minutes
6. **Maintainability**: Code is clean enough to extend easily

---

## Notes for AI Development

1. **One Task at a Time**: Complete and test each component before moving on
2. **Start Simple**: Begin with minimal implementations, add features incrementally
3. **Test Everything**: Write tests alongside code, not after
4. **Follow the Plan**: Don't deviate from the architecture defined here
5. **Handle Errors**: Assume everything can fail, handle it gracefully
6. **Log Appropriately**: Enough to debug, not so much to fill disks
7. **Ask Questions**: If something is unclear, note it in NEXT_STEPS.md

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-12-22  
**Status**: Active Development
