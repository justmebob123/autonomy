#!/bin/bash
#===============================================================================
# STORAGE RECONFIGURATION FOR OLLAMA SERVER
#
# This script:
# 1. Creates a new logical volume from unused LVM space
# 2. Mounts it at /data
# 3. Configures Ollama to store models in /data/ollama
# 4. Configures Docker to store data in /data/docker
#
# Run as root on hq-ce-ollama01
#===============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_cmd() { echo -e "${YELLOW}[CMD]${NC} $1"; }

#===============================================================================
# CONFIGURATION
#===============================================================================

# Volume Group name (detected from your system)
VG_NAME="cs_hq-ce-ollama01"

# New Logical Volume name
LV_NAME="data"

# Mount point
MOUNT_POINT="/data"

# Size to allocate (use all free space, or specify like "500G")
LV_SIZE="100%FREE"

#===============================================================================
# PRE-FLIGHT CHECKS
#===============================================================================

preflight_checks() {
    echo
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}     STORAGE RECONFIGURATION FOR OLLAMA/DOCKER${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo
    
    # Must be root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
    
    # Check if VG exists
    if ! vgs "$VG_NAME" &>/dev/null; then
        log_error "Volume group '$VG_NAME' not found"
        log_info "Available volume groups:"
        vgs
        exit 1
    fi
    
    log_success "Volume group '$VG_NAME' found"
}

#===============================================================================
# ANALYSIS
#===============================================================================

analyze_storage() {
    echo
    log_info "CURRENT STORAGE ANALYSIS"
    echo "─────────────────────────────────────────────────────────────────────"
    echo
    
    echo "Volume Group Status:"
    vgs "$VG_NAME"
    echo
    
    echo "Logical Volumes:"
    lvs "$VG_NAME"
    echo
    
    echo "Free Space in VG:"
    FREE_SPACE=$(vgs --noheadings -o vg_free --units g "$VG_NAME" | tr -d ' ')
    echo "  Available: $FREE_SPACE"
    echo
    
    echo "Current Disk Usage:"
    df -h / /boot 2>/dev/null || df -h /
    echo
    
    echo "Ollama Current Location:"
    if [ -d /usr/share/ollama ]; then
        du -sh /usr/share/ollama 2>/dev/null || echo "  /usr/share/ollama exists"
        ls -la /usr/share/ollama/ 2>/dev/null | head -5
    else
        echo "  Not found at /usr/share/ollama"
    fi
    echo
    
    echo "Docker Current Location:"
    if [ -d /var/lib/docker ]; then
        du -sh /var/lib/docker 2>/dev/null || echo "  /var/lib/docker exists"
    else
        echo "  Docker not installed or no data"
    fi
    echo
    
    echo "─────────────────────────────────────────────────────────────────────"
}

#===============================================================================
# STEP 1: CREATE LOGICAL VOLUME
#===============================================================================

create_logical_volume() {
    echo
    log_info "STEP 1: Creating Logical Volume"
    echo "─────────────────────────────────────────────────────────────────────"
    
    # Check if LV already exists
    if lvs "$VG_NAME/$LV_NAME" &>/dev/null; then
        log_warn "Logical volume '$LV_NAME' already exists"
        lvs "$VG_NAME/$LV_NAME"
        return 0
    fi
    
    log_cmd "lvcreate -l $LV_SIZE -n $LV_NAME $VG_NAME"
    echo
    read -p "Create logical volume using all free space? [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lvcreate -l "$LV_SIZE" -n "$LV_NAME" "$VG_NAME"
        log_success "Logical volume created"
    else
        log_warn "Skipped LV creation"
        return 1
    fi
}

#===============================================================================
# STEP 2: FORMAT FILESYSTEM
#===============================================================================

format_filesystem() {
    echo
    log_info "STEP 2: Formatting Filesystem"
    echo "─────────────────────────────────────────────────────────────────────"
    
    LV_PATH="/dev/$VG_NAME/$LV_NAME"
    
    # Check if already formatted
    if blkid "$LV_PATH" | grep -q "TYPE="; then
        log_warn "Filesystem already exists on $LV_PATH"
        blkid "$LV_PATH"
        read -p "Reformat? THIS WILL DESTROY DATA! [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return 0
        fi
    fi
    
    log_cmd "mkfs.xfs $LV_PATH"
    echo
    read -p "Format with XFS? [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        mkfs.xfs "$LV_PATH"
        log_success "Filesystem created"
    else
        log_warn "Skipped formatting"
        return 1
    fi
}

#===============================================================================
# STEP 3: CREATE MOUNT POINT AND MOUNT
#===============================================================================

setup_mount() {
    echo
    log_info "STEP 3: Setting Up Mount Point"
    echo "─────────────────────────────────────────────────────────────────────"
    
    LV_PATH="/dev/$VG_NAME/$LV_NAME"
    
    # Create mount point
    if [ ! -d "$MOUNT_POINT" ]; then
        log_cmd "mkdir -p $MOUNT_POINT"
        mkdir -p "$MOUNT_POINT"
        log_success "Created $MOUNT_POINT"
    else
        log_warn "$MOUNT_POINT already exists"
    fi
    
    # Check if already mounted
    if mountpoint -q "$MOUNT_POINT"; then
        log_warn "$MOUNT_POINT is already mounted"
        df -h "$MOUNT_POINT"
        return 0
    fi
    
    # Mount it
    log_cmd "mount $LV_PATH $MOUNT_POINT"
    mount "$LV_PATH" "$MOUNT_POINT"
    log_success "Mounted $LV_PATH at $MOUNT_POINT"
    
    # Create subdirectories
    log_info "Creating subdirectories..."
    mkdir -p "$MOUNT_POINT/ollama"
    mkdir -p "$MOUNT_POINT/docker"
    mkdir -p "$MOUNT_POINT/models"
    
    # Set permissions for ollama
    if id ollama &>/dev/null; then
        chown ollama:ollama "$MOUNT_POINT/ollama"
        log_success "Set ownership of $MOUNT_POINT/ollama to ollama:ollama"
    fi
    
    log_success "Subdirectories created"
    ls -la "$MOUNT_POINT/"
}

#===============================================================================
# STEP 4: UPDATE FSTAB
#===============================================================================

update_fstab() {
    echo
    log_info "STEP 4: Updating /etc/fstab"
    echo "─────────────────────────────────────────────────────────────────────"
    
    LV_PATH="/dev/$VG_NAME/$LV_NAME"
    FSTAB_ENTRY="$LV_PATH $MOUNT_POINT xfs defaults 0 0"
    
    # Check if already in fstab
    if grep -q "$MOUNT_POINT" /etc/fstab; then
        log_warn "Entry for $MOUNT_POINT already exists in /etc/fstab"
        grep "$MOUNT_POINT" /etc/fstab
        return 0
    fi
    
    # Backup fstab
    cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)
    log_success "Backed up /etc/fstab"
    
    log_cmd "Adding to /etc/fstab:"
    echo "  $FSTAB_ENTRY"
    echo
    read -p "Add to fstab? [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "" >> /etc/fstab
        echo "# Data partition for Ollama and Docker" >> /etc/fstab
        echo "$FSTAB_ENTRY" >> /etc/fstab
        log_success "Added to /etc/fstab"
        
        # Reload systemd
        systemctl daemon-reload
        log_success "Reloaded systemd"
    else
        log_warn "Skipped fstab update"
    fi
}

#===============================================================================
# STEP 5: CONFIGURE OLLAMA
#===============================================================================

configure_ollama() {
    echo
    log_info "STEP 5: Configuring Ollama"
    echo "─────────────────────────────────────────────────────────────────────"
    
    OLLAMA_DATA="$MOUNT_POINT/ollama"
    OLLAMA_SERVICE="/etc/systemd/system/ollama.service"
    OLLAMA_SERVICE_D="/etc/systemd/system/ollama.service.d"
    
    # Check if Ollama is installed
    if ! command -v ollama &>/dev/null; then
        log_warn "Ollama not installed, skipping configuration"
        return 0
    fi
    
    echo "Current Ollama data location:"
    echo "  OLLAMA_MODELS: ${OLLAMA_MODELS:-/usr/share/ollama/.ollama/models}"
    if [ -d /usr/share/ollama/.ollama ]; then
        du -sh /usr/share/ollama/.ollama 2>/dev/null || echo "  (exists)"
    fi
    echo
    
    # Create override directory
    mkdir -p "$OLLAMA_SERVICE_D"
    
    # Create override file
    OVERRIDE_FILE="$OLLAMA_SERVICE_D/override.conf"
    
    cat > "$OVERRIDE_FILE" << EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_MODELS=$OLLAMA_DATA/models"
EOF
    
    log_success "Created $OVERRIDE_FILE"
    cat "$OVERRIDE_FILE"
    echo
    
    # Move existing models if they exist
    if [ -d /usr/share/ollama/.ollama/models ] && [ "$(ls -A /usr/share/ollama/.ollama/models 2>/dev/null)" ]; then
        echo "Existing models found at /usr/share/ollama/.ollama/models"
        du -sh /usr/share/ollama/.ollama/models
        echo
        read -p "Move existing models to $OLLAMA_DATA/models? [y/N] " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Stopping Ollama..."
            systemctl stop ollama 2>/dev/null || true
            
            log_info "Moving models..."
            mkdir -p "$OLLAMA_DATA/models"
            
            # Use rsync for safe copy
            if command -v rsync &>/dev/null; then
                rsync -av /usr/share/ollama/.ollama/models/ "$OLLAMA_DATA/models/"
            else
                cp -av /usr/share/ollama/.ollama/models/* "$OLLAMA_DATA/models/"
            fi
            
            chown -R ollama:ollama "$OLLAMA_DATA"
            log_success "Models moved"
            
            # Keep old location as backup for now
            mv /usr/share/ollama/.ollama/models /usr/share/ollama/.ollama/models.old
            log_info "Old models backed up to /usr/share/ollama/.ollama/models.old"
        fi
    else
        mkdir -p "$OLLAMA_DATA/models"
        chown -R ollama:ollama "$OLLAMA_DATA"
    fi
    
    # Reload and restart
    log_info "Reloading systemd and restarting Ollama..."
    systemctl daemon-reload
    systemctl restart ollama
    
    # Verify
    sleep 2
    if systemctl is-active --quiet ollama; then
        log_success "Ollama is running"
        echo
        echo "Verify new location:"
        ollama list 2>/dev/null || echo "  (no models yet)"
        echo
        echo "Models will now be stored in: $OLLAMA_DATA/models"
    else
        log_error "Ollama failed to start!"
        journalctl -u ollama --no-pager -n 20
    fi
}

#===============================================================================
# STEP 6: CONFIGURE DOCKER
#===============================================================================

configure_docker() {
    echo
    log_info "STEP 6: Configuring Docker"
    echo "─────────────────────────────────────────────────────────────────────"
    
    DOCKER_DATA="$MOUNT_POINT/docker"
    DOCKER_CONFIG="/etc/docker/daemon.json"
    
    # Check if Docker is installed
    if ! command -v docker &>/dev/null; then
        log_warn "Docker not installed, skipping configuration"
        echo
        echo "If you install Docker later, add this to $DOCKER_CONFIG:"
        echo '{'
        echo "  \"data-root\": \"$DOCKER_DATA\""
        echo '}'
        return 0
    fi
    
    echo "Current Docker data location:"
    docker info 2>/dev/null | grep "Docker Root Dir" || echo "  /var/lib/docker (default)"
    if [ -d /var/lib/docker ]; then
        du -sh /var/lib/docker 2>/dev/null || echo "  (exists)"
    fi
    echo
    
    # Create or update daemon.json
    mkdir -p /etc/docker
    
    if [ -f "$DOCKER_CONFIG" ]; then
        log_warn "$DOCKER_CONFIG already exists"
        cat "$DOCKER_CONFIG"
        echo
        read -p "Overwrite with new configuration? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Manual configuration required. Add:"
            echo "  \"data-root\": \"$DOCKER_DATA\""
            return 0
        fi
        cp "$DOCKER_CONFIG" "$DOCKER_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Write new config
    cat > "$DOCKER_CONFIG" << EOF
{
  "data-root": "$DOCKER_DATA",
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
    
    log_success "Created $DOCKER_CONFIG"
    cat "$DOCKER_CONFIG"
    echo
    
    # Move existing Docker data if present
    if [ -d /var/lib/docker ] && [ "$(ls -A /var/lib/docker 2>/dev/null)" ]; then
        echo "Existing Docker data found at /var/lib/docker"
        du -sh /var/lib/docker
        echo
        read -p "Move existing Docker data to $DOCKER_DATA? [y/N] " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Stopping Docker..."
            systemctl stop docker docker.socket containerd 2>/dev/null || true
            
            log_info "Moving Docker data (this may take a while)..."
            if command -v rsync &>/dev/null; then
                rsync -av /var/lib/docker/ "$DOCKER_DATA/"
            else
                cp -av /var/lib/docker/* "$DOCKER_DATA/"
            fi
            
            log_success "Docker data moved"
            
            # Keep old location as backup
            mv /var/lib/docker /var/lib/docker.old
            log_info "Old Docker data backed up to /var/lib/docker.old"
        fi
    fi
    
    # Restart Docker
    log_info "Restarting Docker..."
    systemctl daemon-reload
    systemctl start docker
    
    # Verify
    sleep 2
    if systemctl is-active --quiet docker; then
        log_success "Docker is running"
        echo
        echo "Verify new location:"
        docker info 2>/dev/null | grep "Docker Root Dir"
    else
        log_error "Docker failed to start!"
        journalctl -u docker --no-pager -n 20
    fi
}

#===============================================================================
# FINAL SUMMARY
#===============================================================================

show_summary() {
    echo
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                         CONFIGURATION COMPLETE${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo
    
    echo "STORAGE LAYOUT:"
    echo "─────────────────────────────────────────────────────────────────────"
    df -h "$MOUNT_POINT" / 2>/dev/null
    echo
    
    echo "DIRECTORY STRUCTURE:"
    echo "─────────────────────────────────────────────────────────────────────"
    ls -la "$MOUNT_POINT/" 2>/dev/null
    echo
    
    echo "MOUNT CONFIGURATION (/etc/fstab):"
    echo "─────────────────────────────────────────────────────────────────────"
    grep -v "^#" /etc/fstab | grep -v "^$"
    echo
    
    echo "SERVICE STATUS:"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -n "  Ollama: "
    systemctl is-active ollama 2>/dev/null || echo "not installed"
    echo -n "  Docker: "
    systemctl is-active docker 2>/dev/null || echo "not installed"
    echo
    
    echo "PATHS:"
    echo "─────────────────────────────────────────────────────────────────────"
    echo "  Mount Point:    $MOUNT_POINT"
    echo "  Ollama Models:  $MOUNT_POINT/ollama/models"
    echo "  Docker Data:    $MOUNT_POINT/docker"
    echo
    
    echo "CLEANUP (optional, after verifying everything works):"
    echo "─────────────────────────────────────────────────────────────────────"
    echo "  # Remove old Ollama models backup:"
    echo "  rm -rf /usr/share/ollama/.ollama/models.old"
    echo
    echo "  # Remove old Docker data backup:"
    echo "  rm -rf /var/lib/docker.old"
    echo
    
    echo "TO VERIFY OLLAMA IS USING NEW LOCATION:"
    echo "─────────────────────────────────────────────────────────────────────"
    echo "  ollama pull llama3.2:latest"
    echo "  ls -la $MOUNT_POINT/ollama/models/"
    echo
}

#===============================================================================
# MANUAL COMMANDS (for reference)
#===============================================================================

show_manual_commands() {
    cat << 'EOF'

═══════════════════════════════════════════════════════════════════════
  MANUAL COMMANDS (if you prefer to run step-by-step)
═══════════════════════════════════════════════════════════════════════

# 1. Check current LVM status
vgs
lvs
vgdisplay cs_hq-ce-ollama01

# 2. Create logical volume using all free space
lvcreate -l 100%FREE -n data cs_hq-ce-ollama01

# 3. Format with XFS
mkfs.xfs /dev/cs_hq-ce-ollama01/data

# 4. Create mount point and mount
mkdir -p /data
mount /dev/cs_hq-ce-ollama01/data /data

# 5. Create subdirectories
mkdir -p /data/ollama /data/docker /data/models
chown ollama:ollama /data/ollama

# 6. Add to /etc/fstab
echo "/dev/cs_hq-ce-ollama01/data /data xfs defaults 0 0" >> /etc/fstab

# 7. Configure Ollama
mkdir -p /etc/systemd/system/ollama.service.d
cat > /etc/systemd/system/ollama.service.d/override.conf << CONF
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
Environment="OLLAMA_MODELS=/data/ollama/models"
CONF

# 8. Move existing Ollama models (if any)
systemctl stop ollama
rsync -av /usr/share/ollama/.ollama/models/ /data/ollama/models/
chown -R ollama:ollama /data/ollama
systemctl daemon-reload
systemctl restart ollama

# 9. Configure Docker
cat > /etc/docker/daemon.json << CONF
{
  "data-root": "/data/docker"
}
CONF

# 10. Move existing Docker data (if any)
systemctl stop docker docker.socket containerd
rsync -av /var/lib/docker/ /data/docker/
systemctl daemon-reload
systemctl start docker

# 11. Verify
df -h /data
ollama list
docker info | grep "Docker Root Dir"

EOF
}

#===============================================================================
# MAIN
#===============================================================================

main() {
    case "${1:-}" in
        --manual)
            show_manual_commands
            exit 0
            ;;
        --analyze)
            preflight_checks
            analyze_storage
            exit 0
            ;;
        --help|-h)
            echo "Usage: $0 [--analyze|--manual|--help]"
            echo
            echo "  (no args)   Run interactive setup"
            echo "  --analyze   Only analyze current storage"
            echo "  --manual    Show manual commands"
            echo "  --help      Show this help"
            exit 0
            ;;
    esac
    
    preflight_checks
    analyze_storage
    
    echo
    read -p "Proceed with storage reconfiguration? [y/N] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    
    create_logical_volume
    format_filesystem
    setup_mount
    update_fstab
    configure_ollama
    configure_docker
    show_summary
}

main "$@"
