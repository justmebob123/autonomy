# MASTER PLAN: Autonomous System Administration Suite (ASAS)

> **⚠️ READ-ONLY FOR AI PIPELINE**  
> This document defines the complete specification for the system administration suite.
> The AI pipeline reads this file but NEVER modifies it.
> Human maintainers update this document to change project direction.

---

## 🚨 CRITICAL DEVELOPMENT RULES

### File Existence Protocol

**BEFORE creating or modifying ANY file, the AI MUST:**

1. **Check if file exists** using file reading tools
2. **Request file content** if it exists
3. **Analyze current state**:
   - If file is complete and correct → Mark task as COMPLETED
   - If file has bugs/issues → Route to debugging phase
   - If file needs enhancements → Route to QA phase for review
   - If file is missing required functionality → Implement additions only

4. **NEVER make trivial changes** like:
   - Adding docstring comments when code is already documented
   - Reformatting without functional changes
   - Changing variable names without reason
   - Adding type hints to already-typed code

5. **Share context in conversation**:
   - Include relevant file content in responses
   - Explain what exists vs what needs to be built
   - Show diffs for proposed changes
   - Justify why changes are necessary

### Task Completion Criteria

A task is COMPLETED when:
- ✅ File exists with required functionality
- ✅ Code passes quality checks (no bugs, good complexity)
- ✅ File meets the specification in this MASTER_PLAN
- ✅ No enhancements are needed for current phase

A task needs DEBUGGING when:
- ❌ File has syntax errors
- ❌ File has logic bugs
- ❌ File fails quality checks
- ❌ File doesn't meet specification

A task needs ENHANCEMENT when:
- 🔄 File exists but missing features from spec
- 🔄 File needs performance improvements
- 🔄 File needs additional error handling
- 🔄 File needs better documentation

### Workflow for Existing Files

```
1. Read file → 2. Analyze state → 3. Decide action:
   
   ├─ File complete & correct → MARK COMPLETED
   ├─ File has bugs → ROUTE TO DEBUGGING
   ├─ File needs features → IMPLEMENT ADDITIONS
   └─ File needs review → ROUTE TO QA
```

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
**Priority: HIGH | Phase: 2**

**Required Files:**
- `monitors/system.py` - System metrics monitor
- `tests/test_monitors/test_system.py` - Unit tests

**Functionality:**
- Monitor CPU, memory, swap, and load average
- Track process counts and zombie processes
- Monitor system uptime and recent reboots
- Detect runaway processes consuming excessive resources

**Completion Criteria:**
- All metrics collected accurately
- Thresholds configurable via config
- Returns CheckResult objects
- 80%+ test coverage

### 2. Disk and Storage Management
**Priority: HIGH | Phase: 2**

**Required Files:**
- `monitors/disk.py` - Disk monitoring
- `tests/test_monitors/test_disk.py` - Unit tests

**Functionality:**
- Monitor disk usage on all mounted filesystems
- Track inode usage (often overlooked cause of "disk full" issues)
- Monitor disk I/O performance and latency
- Integrate with SMART for disk health prediction
- Alert on approaching capacity thresholds (warning: 80%, critical: 90%)
- Identify large files and directories consuming space
- Track disk usage trends over time

**Completion Criteria:**
- All filesystems monitored
- Inode tracking working
- SMART integration optional but functional
- Trend analysis stores data in DB

### 3. Service and Process Monitoring
**Priority: HIGH | Phase: 2**

**Required Files:**
- `monitors/services.py` - Service monitoring
- `tests/test_monitors/test_services.py` - Unit tests

**Functionality:**
- Monitor systemd service status
- Detect failed and crashed services
- Optional auto-restart of critical services
- Track service resource consumption
- Monitor critical processes (sshd, cron, etc.)
- Detect services listening on unexpected ports

**Completion Criteria:**
- Systemd integration working
- Auto-restart configurable and safe
- Process monitoring accurate
- Port detection functional

### 4. Security Monitoring
**Priority: MEDIUM | Phase: 4**

**Required Files:**
- `monitors/security.py` - Security monitoring
- `tests/test_monitors/test_security.py` - Unit tests

**Functionality:**
- Parse /var/log/auth.log and /var/log/secure for authentication events
- Detect SSH brute force attacks (multiple failed logins)
- Monitor sudo usage and privilege escalation
- Track user login/logout events
- Detect new user account creation
- Monitor changes to critical system files (/etc/passwd, /etc/shadow, /etc/sudoers)
- Check for unauthorized SUID/SGID binaries
- Monitor open ports and network connections

**Completion Criteria:**
- Log parsing accurate
- Brute force detection working
- File integrity checks functional
- SUID/SGID detection working

### 5. Log Analysis
**Priority: MEDIUM | Phase: 4**

**Required Files:**
- `monitors/logs.py` - Log analysis
- `tests/test_monitors/test_logs.py` - Unit tests

**Functionality:**
- Parse syslog, journald, and application logs
- Pattern matching for errors, warnings, and critical events
- Configurable regex patterns for custom log parsing
- Log rotation monitoring
- Aggregate and summarize log events
- Detect log anomalies (sudden spike in errors)

**Completion Criteria:**
- Multiple log sources supported
- Regex patterns configurable
- Anomaly detection working
- Performance acceptable

### 6. Firewall Monitoring
**Priority: LOW | Phase: 5**

**Required Files:**
- `monitors/firewall.py` - Firewall monitoring
- `tests/test_monitors/test_firewall.py` - Unit tests

**Functionality:**
- Monitor iptables/nftables/firewalld status
- Detect rule changes
- Backup current firewall rules
- Alert on firewall being disabled
- Track blocked connection attempts

**Completion Criteria:**
- All firewall types supported
- Rule backup working
- Change detection accurate

### 7. Hardware Health
**Priority: LOW | Phase: 5**

**Required Files:**
- `monitors/hardware.py` - Hardware monitoring
- `tests/test_monitors/test_hardware.py` - Unit tests

**Functionality:**
- SMART disk monitoring for HDD/SSD health
- CPU temperature monitoring (where available)
- Memory error detection via dmesg/mcelog
- RAID array status monitoring (mdadm, hardware RAID)
- Network interface status and error counters
- Power supply and UPS status (where available)

**Completion Criteria:**
- SMART integration working
- Temperature monitoring optional
- RAID detection functional
- Graceful degradation when hardware unavailable

### 8. Network Monitoring
**Priority: MEDIUM | Phase: 3**

**Required Files:**
- `monitors/network.py` - Network monitoring
- `tests/test_monitors/test_network.py` - Unit tests

**Functionality:**
- Monitor network interface status (up/down)
- Track bandwidth usage per interface
- Detect network errors and dropped packets
- Monitor DNS resolution
- Check connectivity to critical endpoints
- Track established connections and connection states

**Completion Criteria:**
- Interface monitoring working
- Bandwidth tracking accurate
- DNS checks functional
- Connectivity tests working

### 9. Alerting System
**Priority: HIGH | Phase: 3**

**Required Files:**
- `alerts/manager.py` - Alert management
- `alerts/email.py` - Email alerts
- `alerts/webhook.py` - Webhook alerts
- `alerts/local.py` - Local logging
- `tests/test_alerts/` - Alert tests

**Functionality:**
- Email notifications via SMTP
- Webhook notifications (Slack, Discord, Teams, custom)
- Local logging of all alerts
- Alert aggregation (don't spam on repeated issues)
- Alert escalation (warning → critical)
- Configurable alert thresholds per check
- Quiet hours / maintenance windows

**Completion Criteria:**
- All alert channels working
- Aggregation prevents spam
- Escalation logic correct
- Quiet hours respected

### 10. Reporting and History
**Priority: MEDIUM | Phase: 6**

**Required Files:**
- `reports/generator.py` - Report generation
- `core/database.py` - History storage
- `tests/test_reports/` - Report tests

**Functionality:**
- Store historical metrics in SQLite database
- Generate daily/weekly summary reports
- Trend analysis for capacity planning
- Export data in JSON/CSV formats
- Optional web dashboard for visualization

**Completion Criteria:**
- Database schema complete
- Report generation working
- Trend analysis functional
- Export formats working

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
│   ├── config.py               # Configuration loader with validation ✅ EXISTS
│   ├── logger.py               # Centralized logging setup
│   ├── scheduler.py            # APScheduler-based task scheduler
│   ├── database.py             # SQLite database for history
│   └── utils.py                # Shared utility functions ✅ EXISTS
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
├── scripts/
│   ├── install.sh              # Installation script
│   └── asas.service            # Systemd service file
├── requirements.txt
├── pyproject.toml
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**Legend:**
- ✅ EXISTS - File already created
- 🔄 IN PROGRESS - File partially complete
- ❌ MISSING - File not yet created

---

## Component Specifications

### Core Components

#### config.py - Configuration Loader ✅ EXISTS
**Status: REVIEW NEEDED**

**Current State:**
- File exists at `core/config.py`
- Has ConfigManager class with load_config, get_config, validate_config
- Uses Pydantic for validation
- Handles JSON configuration files

**Required Functionality:**
```python
# Must implement:
- load_config(path: str) -> Config
- validate_config(config: dict) -> bool
- merge_configs(base: dict, override: dict) -> dict
- get_env_overrides() -> dict  # Support ENV variable overrides
- Config dataclass with typed fields
```

**Action Required:**
1. Read existing file
2. Check if all required methods exist
3. If complete → Mark COMPLETED
4. If missing features → Implement additions
5. If has bugs → Route to debugging

#### logger.py - Logging Setup ❌ MISSING
**Priority: HIGH | Phase: 1**

**Required Functionality:**
```python
# Must implement:
- setup_logging(config: LogConfig) -> logging.Logger
- Support for: console, file, syslog outputs
- Log rotation (size-based and time-based)
- Structured logging with JSON option
- Context managers for operation timing
```

**Implementation Notes:**
- Use Python's logging module
- Support multiple handlers simultaneously
- Configurable log levels per handler
- Thread-safe logging

#### scheduler.py - Task Scheduler ❌ MISSING
**Priority: HIGH | Phase: 1**

**Required Functionality:**
```python
# Must implement:
- Scheduler class wrapping APScheduler
- add_monitor(monitor: BaseMonitor, interval: int)
- remove_monitor(name: str)
- pause() / resume()
- get_status() -> dict
- Graceful shutdown handling
```

**Implementation Notes:**
- Use APScheduler BackgroundScheduler
- Handle monitor exceptions gracefully
- Support dynamic interval changes
- Proper cleanup on shutdown

#### database.py - History Storage ❌ MISSING
**Priority: MEDIUM | Phase: 2**

**Required Functionality:**
```python
# Must implement:
- Database class for SQLite operations
- store_metric(monitor: str, metric: str, value: float, timestamp: datetime)
- get_metrics(monitor: str, metric: str, start: datetime, end: datetime) -> List
- cleanup_old_data(retention_days: int)
- Schema migration support
```

**Implementation Notes:**
- Use aiosqlite for async operations
- Create indexes for query performance
- Handle concurrent access safely
- Support schema versioning

#### utils.py - Shared Utilities ✅ EXISTS
**Status: REVIEW NEEDED**

**Current State:**
- File exists at `core/utils.py`
- Has chunk_list function (unused - dead code)

**Required Functionality:**
```python
# Must implement:
- format_bytes(bytes: int) -> str  # Human-readable sizes
- format_duration(seconds: float) -> str  # Human-readable time
- safe_divide(a: float, b: float) -> float  # Avoid division by zero
- parse_size(size_str: str) -> int  # Parse "10GB" to bytes
- get_hostname() -> str  # Get system hostname
```

**Action Required:**
1. Read existing file
2. Remove dead code (chunk_list)
3. Implement required utility functions
4. Add unit tests

### Monitor Base Class

#### base.py - Abstract Base Monitor ❌ MISSING
**Priority: CRITICAL | Phase: 1**

**Required Implementation:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime

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
        thresholds = self.config.get('thresholds', {})
        return {
            'warning': thresholds.get(f'{check_name}_warning'),
            'critical': thresholds.get(f'{check_name}_critical')
        }
    
    def is_enabled(self) -> bool:
        """Check if this monitor is enabled."""
        return self.enabled
```

**Implementation Notes:**
- This is the foundation for ALL monitors
- Must be implemented FIRST before any monitor
- All monitors inherit from this class
- Provides consistent interface

---

## Development Phases

### Phase 1: Foundation (CURRENT PRIORITY)
**Goal: Core infrastructure that all other components depend on**

**Required Files (in order):**
1. ✅ `core/config.py` - EXISTS, needs review
2. ❌ `core/logger.py` - MISSING, create next
3. ❌ `monitors/base.py` - MISSING, critical dependency
4. ✅ `core/utils.py` - EXISTS, needs cleanup
5. ❌ `core/scheduler.py` - MISSING
6. ❌ `core/database.py` - MISSING

**Completion Criteria:**
- All core files exist and pass tests
- Configuration system fully functional
- Logging system working
- Base monitor class ready for inheritance
- Scheduler can run monitors
- Database can store metrics

**DO NOT PROCEED to Phase 2 until Phase 1 is 100% complete!**

### Phase 2: Core Monitors
**Goal: Essential monitoring functionality**

**Required Files:**
1. `monitors/system.py` - System metrics
2. `monitors/disk.py` - Disk monitoring
3. `monitors/services.py` - Service monitoring
4. `alerts/local.py` - Basic local logging

**Completion Criteria:**
- System monitoring working
- Disk monitoring working
- Service monitoring working
- Alerts logged locally

### Phase 3: Alerting
**Goal: Multi-channel alert delivery**

**Required Files:**
1. `alerts/manager.py` - Alert management
2. `alerts/email.py` - Email alerts
3. `alerts/webhook.py` - Webhook alerts

**Completion Criteria:**
- Email alerts working
- Webhook alerts working
- Alert aggregation prevents spam

### Phase 4: Security & Logs
**Goal: Security monitoring and log analysis**

**Required Files:**
1. `monitors/security.py` - Security monitoring
2. `monitors/logs.py` - Log analysis

**Completion Criteria:**
- Security monitoring working
- Log analysis functional
- File integrity checks working

### Phase 5: Advanced Monitors
**Goal: Additional monitoring capabilities**

**Required Files:**
1. `monitors/firewall.py` - Firewall monitoring
2. `monitors/hardware.py` - Hardware health
3. `monitors/network.py` - Network monitoring

**Completion Criteria:**
- All monitors implemented
- All monitors tested
- All monitors documented

### Phase 6: Polish
**Goal: Production readiness**

**Required Files:**
1. `reports/generator.py` - Reporting
2. `cli/commands.py` - CLI interface
3. `scripts/install.sh` - Installation
4. `scripts/asas.service` - Systemd service

**Completion Criteria:**
- Full documentation
- Installation scripts
- Systemd integration
- Package ready for distribution

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

### CRITICAL: File Existence Workflow

**ALWAYS follow this workflow:**

```
START TASK
    ↓
Check if file exists
    ↓
    ├─ File DOES NOT exist
    │   ↓
    │   Create file with full implementation
    │   ↓
    │   Write tests
    │   ↓
    │   Mark task COMPLETED
    │
    └─ File EXISTS
        ↓
        Read file content
        ↓
        Analyze current state
        ↓
        ├─ File is complete & correct
        │   ↓
        │   Mark task COMPLETED (no changes needed)
        │
        ├─ File has bugs/errors
        │   ↓
        │   Route to DEBUGGING phase
        │   ↓
        │   Fix bugs
        │   ↓
        │   Mark task COMPLETED
        │
        ├─ File needs enhancements
        │   ↓
        │   Route to QA phase for review
        │   ↓
        │   Implement additions only
        │   ↓
        │   Mark task COMPLETED
        │
        └─ File needs minor updates
            ↓
            Make ONLY necessary changes
            ↓
            Explain why changes are needed
            ↓
            Mark task COMPLETED
```

### DO NOT:
- ❌ Make trivial changes to existing files
- ❌ Add comments to already-documented code
- ❌ Reformat code without functional changes
- ❌ Modify files that are already correct
- ❌ Create files without checking if they exist first

### DO:
- ✅ Read existing files before making changes
- ✅ Share file content in conversation
- ✅ Explain what exists vs what needs to be built
- ✅ Mark tasks COMPLETED when files are correct
- ✅ Route to appropriate phase (debugging/QA) when needed
- ✅ Make only necessary, functional changes

### Example Good Behavior:

```
Task: Implement config.py

1. Check if core/config.py exists
2. Read file content
3. Analyze:
   - Has ConfigManager class ✅
   - Has load_config method ✅
   - Has validate_config method ✅
   - Missing: merge_configs method ❌
   - Missing: get_env_overrides method ❌
4. Action: Implement ONLY the 2 missing methods
5. Explain: "File exists with 3/5 required methods. Adding merge_configs and get_env_overrides."
6. Mark COMPLETED after adding methods
```

### Example Bad Behavior:

```
Task: Implement config.py

1. Create core/config.py (without checking if it exists)
2. Write entire file from scratch
3. Overwrite existing working code
4. Add docstrings to already-documented functions
5. Change variable names for no reason
6. Result: Wasted time, potential bugs introduced
```

---

**Document Version**: 2.0.0  
**Last Updated**: 2024-12-29  
**Status**: Active Development - Phase 1 (Foundation)