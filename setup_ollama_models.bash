#!/bin/bash
#===============================================================================
# COMPLETE STORAGE SETUP AND DATA MIGRATION
# 
# For CentOS Stream 9 / RHEL 9
#
# This script:
# 1. Sets up LVM on /dev/sdb2 (handles RHEL9 devices file issue)
# 2. Creates and mounts /data filesystem
# 3. Migrates Ollama data with proper permissions
# 4. Migrates Docker data completely
# 5. Configures Git to use data partition
# 6. Updates all service configurations
# 7. Verifies everything works
#
# Run as root: bash setup_storage.sh
#===============================================================================

set -euo pipefail

#===============================================================================
# CONFIGURATION
#===============================================================================

DATA_PARTITION="/dev/sdb2"
MOUNT_POINT="/data"
VG_NAME="vg_data"
LV_NAME="lv_data"

# Service data directories
OLLAMA_NEW_HOME="$MOUNT_POINT/ollama"
DOCKER_NEW_HOME="$MOUNT_POINT/docker"
GIT_NEW_HOME="$MOUNT_POINT/git"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

#===============================================================================
# LOGGING
#===============================================================================

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { 
    echo
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo
}

#===============================================================================
# HELPER FUNCTIONS
#===============================================================================

get_dir_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        du -sh "$dir" 2>/dev/null | cut -f1
    else
        echo "0"
    fi
}

get_user_info() {
    local username="$1"
    if id "$username" &>/dev/null; then
        local uid=$(id -u "$username")
        local gid=$(id -g "$username")
        local home=$(getent passwd "$username" | cut -d: -f6)
        echo "$uid:$gid:$home"
    else
        echo ""
    fi
}

service_is_active() {
    systemctl is-active --quiet "$1" 2>/dev/null
}

safe_stop_service() {
    local service="$1"
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        log_info "Stopping $service..."
        systemctl stop "$service"
        sleep 2
    fi
}

safe_start_service() {
    local service="$1"
    log_info "Starting $service..."
    systemctl daemon-reload
    systemctl start "$service"
    sleep 2
    if systemctl is-active --quiet "$service"; then
        log_success "$service is running"
        return 0
    else
        log_error "$service failed to start"
        return 1
    fi
}

#===============================================================================
# PRE-FLIGHT CHECKS
#===============================================================================

preflight_checks() {
    log_section "PRE-FLIGHT CHECKS"
    
    # Must be root
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
        exit 1
    fi
    log_success "Running as root"
    
    # Check OS
    if [ -f /etc/system-release ]; then
        cat /etc/system-release
    fi
    
    # Check partition exists
    if [ ! -b "$DATA_PARTITION" ]; then
        log_error "Partition $DATA_PARTITION not found"
        exit 1
    fi
    log_success "Partition $DATA_PARTITION exists"
    
    # Check required tools
    for tool in rsync lvcreate mkfs.xfs; do
        if ! command -v "$tool" &>/dev/null; then
            log_error "Required tool '$tool' not found"
            exit 1
        fi
    done
    log_success "Required tools available"
    
    # Analyze current data sizes
    echo
    log_info "Current data sizes:"
    echo "  Ollama (/usr/share/ollama): $(get_dir_size /usr/share/ollama)"
    echo "  Ollama (~ollama):           $(get_dir_size /home/ollama 2>/dev/null || echo 'N/A')"
    echo "  Docker (/var/lib/docker):   $(get_dir_size /var/lib/docker)"
    echo "  Root filesystem usage:"
    df -h / | tail -1 | awk '{print "    Used: "$3" / "$2" ("$5" full)"}'
    echo
    
    # Check Ollama user
    if id ollama &>/dev/null; then
        local ollama_info=$(get_user_info ollama)
        log_success "Ollama user found: UID:GID = $(echo $ollama_info | cut -d: -f1-2)"
        log_info "Ollama home: $(echo $ollama_info | cut -d: -f3)"
    else
        log_warn "Ollama user not found (will be created when Ollama is installed)"
    fi
    
    # Show what services are running
    echo
    log_info "Service status:"
    echo -n "  Ollama: "
    systemctl is-active ollama 2>/dev/null || echo "not running/installed"
    echo -n "  Docker: "
    systemctl is-active docker 2>/dev/null || echo "not running/installed"
    echo -n "  Containerd: "
    systemctl is-active containerd 2>/dev/null || echo "not running/installed"
    echo
}

#===============================================================================
# STEP 1: FIX LVM DEVICES FILE (RHEL 9 ISSUE)
#===============================================================================

fix_lvm_devices_file() {
    log_section "STEP 1: FIX LVM DEVICES FILE"
    
    # Check if device is already recognized
    if pvs "$DATA_PARTITION" &>/dev/null; then
        log_success "LVM already recognizes $DATA_PARTITION"
        return 0
    fi
    
    log_info "Device not in LVM devices file (CentOS Stream 9 issue)"
    
    # Method 1: Add device directly
    log_info "Trying: lvmdevices --adddev $DATA_PARTITION"
    if lvmdevices --adddev "$DATA_PARTITION" 2>/dev/null; then
        log_success "Added via lvmdevices --adddev"
        pvscan 2>/dev/null
        if pvs "$DATA_PARTITION" &>/dev/null; then
            return 0
        fi
    fi
    
    # Method 2: Import all devices
    log_info "Trying: vgimportdevices --all"
    vgimportdevices --all 2>/dev/null || true
    pvscan 2>/dev/null
    if pvs "$DATA_PARTITION" &>/dev/null; then
        log_success "Added via vgimportdevices"
        return 0
    fi
    
    # Method 3: Disable devices file
    log_info "Disabling LVM devices file in lvm.conf"
    if [ -f /etc/lvm/lvm.conf ]; then
        cp /etc/lvm/lvm.conf /etc/lvm/lvm.conf.backup.$(date +%Y%m%d%H%M%S)
        sed -i 's/use_devicesfile = 1/use_devicesfile = 0/g' /etc/lvm/lvm.conf
        
        # Also check for the devices_file setting
        if grep -q "# use_devicesfile" /etc/lvm/lvm.conf; then
            sed -i 's/# use_devicesfile = 1/use_devicesfile = 0/g' /etc/lvm/lvm.conf
        fi
    fi
    
    # Rescan
    pvscan 2>/dev/null || true
    vgscan 2>/dev/null || true
    
    if pvs "$DATA_PARTITION" &>/dev/null; then
        log_success "LVM now recognizes $DATA_PARTITION"
        return 0
    fi
    
    # Still not working - need fresh PV
    log_warn "Existing LVM metadata unrecoverable, will create fresh"
    return 1
}

#===============================================================================
# STEP 2: SETUP LVM
#===============================================================================

setup_lvm() {
    log_section "STEP 2: SETUP LVM STORAGE"
    
    local lv_path="/dev/$VG_NAME/$LV_NAME"
    
    # Check if already fully configured
    if [ -b "$lv_path" ]; then
        log_success "Logical volume $lv_path already exists"
        lvs "$VG_NAME/$LV_NAME"
        return 0
    fi
    
    # Check if VG exists with our PV
    if vgs "$VG_NAME" &>/dev/null; then
        log_info "Volume group $VG_NAME exists"
        
        # Create LV if it doesn't exist
        if ! lvs "$VG_NAME/$LV_NAME" &>/dev/null; then
            log_info "Creating logical volume..."
            lvcreate -l 100%FREE -n "$LV_NAME" "$VG_NAME"
            log_success "Logical volume created"
        fi
        return 0
    fi
    
    # Need to create fresh LVM setup
    log_warn "Creating fresh LVM setup on $DATA_PARTITION"
    log_warn "This will DESTROY any existing data on this partition"
    echo
    read -p "Continue? [y/N] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Aborted by user"
        exit 1
    fi
    
    # Clean existing LVM remnants
    log_info "Cleaning partition..."
    
    # Try to remove from any existing VG
    local old_vg=$(pvs --noheadings -o vg_name "$DATA_PARTITION" 2>/dev/null | tr -d ' ')
    if [ -n "$old_vg" ]; then
        log_info "Removing from old VG: $old_vg"
        vgchange -an "$old_vg" 2>/dev/null || true
        vgremove -f "$old_vg" 2>/dev/null || true
    fi
    
    pvremove -ff "$DATA_PARTITION" 2>/dev/null || true
    wipefs -af "$DATA_PARTITION" 2>/dev/null || true
    dd if=/dev/zero of="$DATA_PARTITION" bs=1M count=10 2>/dev/null || true
    
    log_success "Partition cleaned"
    
    # Create PV
    log_info "Creating Physical Volume..."
    pvcreate -f "$DATA_PARTITION"
    
    # Add to devices file (RHEL 9)
    lvmdevices --adddev "$DATA_PARTITION" 2>/dev/null || true
    
    log_success "PV created"
    
    # Create VG
    log_info "Creating Volume Group: $VG_NAME"
    vgcreate "$VG_NAME" "$DATA_PARTITION"
    log_success "VG created"
    
    # Create LV
    log_info "Creating Logical Volume: $LV_NAME (using all space)"
    lvcreate -l 100%FREE -n "$LV_NAME" "$VG_NAME"
    log_success "LV created"
    
    # Show results
    echo
    pvs
    vgs
    lvs
}

#===============================================================================
# STEP 3: FORMAT AND MOUNT
#===============================================================================

format_and_mount() {
    log_section "STEP 3: FORMAT AND MOUNT FILESYSTEM"
    
    local lv_path="/dev/$VG_NAME/$LV_NAME"
    
    # Check if already formatted
    local current_fs=$(blkid -o value -s TYPE "$lv_path" 2>/dev/null || echo "")
    
    if [ "$current_fs" = "xfs" ]; then
        log_info "Already formatted with XFS"
    else
        log_info "Formatting $lv_path with XFS..."
        mkfs.xfs -f "$lv_path"
        log_success "Formatted"
    fi
    
    # Create mount point
    mkdir -p "$MOUNT_POINT"
    
    # Unmount if mounted
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        log_info "Unmounting existing mount..."
        umount "$MOUNT_POINT" || umount -l "$MOUNT_POINT"
    fi
    
    # Mount
    log_info "Mounting $lv_path at $MOUNT_POINT..."
    mount "$lv_path" "$MOUNT_POINT"
    log_success "Mounted"
    
    # Verify
    df -h "$MOUNT_POINT"
    echo
    
    # Update fstab
    log_info "Updating /etc/fstab..."
    
    # Backup fstab
    cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d%H%M%S)
    
    # Remove any existing entries for this mount point or LV
    sed -i "\|$MOUNT_POINT|d" /etc/fstab
    sed -i "\|$lv_path|d" /etc/fstab
    sed -i "\|$VG_NAME/$LV_NAME|d" /etc/fstab
    
    # Add new entry
    echo "# Data partition for Ollama, Docker, Git" >> /etc/fstab
    echo "$lv_path $MOUNT_POINT xfs defaults,nofail 0 2" >> /etc/fstab
    
    log_success "fstab updated"
    grep -v "^#" /etc/fstab | grep -v "^$"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Test fstab entry
    log_info "Testing fstab entry..."
    umount "$MOUNT_POINT"
    mount "$MOUNT_POINT"
    log_success "fstab entry works"
}

#===============================================================================
# STEP 4: CREATE DIRECTORY STRUCTURE
#===============================================================================

create_directories() {
    log_section "STEP 4: CREATE DIRECTORY STRUCTURE"
    
    # Create main directories
    log_info "Creating directory structure..."
    
    mkdir -p "$OLLAMA_NEW_HOME/models"
    mkdir -p "$DOCKER_NEW_HOME"
    mkdir -p "$GIT_NEW_HOME/repos"
    mkdir -p "$GIT_NEW_HOME/lfs"
    mkdir -p "$MOUNT_POINT/cache"
    mkdir -p "$MOUNT_POINT/tmp"
    
    log_success "Directories created"
    
    # Set Ollama ownership if user exists
    if id ollama &>/dev/null; then
        log_info "Setting Ollama directory ownership..."
        chown -R ollama:ollama "$OLLAMA_NEW_HOME"
        chmod 755 "$OLLAMA_NEW_HOME"
        log_success "Ollama ownership set"
    fi
    
    # Docker directory (root owned)
    chown root:root "$DOCKER_NEW_HOME"
    chmod 711 "$DOCKER_NEW_HOME"
    
    # Git directory (accessible to all)
    chmod 755 "$GIT_NEW_HOME"
    
    # Show structure
    echo
    log_info "Directory structure:"
    ls -la "$MOUNT_POINT/"
}

#===============================================================================
# STEP 5: MIGRATE OLLAMA
#===============================================================================

migrate_ollama() {
    log_section "STEP 5: MIGRATE OLLAMA DATA"
    
    if ! command -v ollama &>/dev/null; then
        log_warn "Ollama not installed, skipping migration"
        log_info "Will configure for future installation"
        create_ollama_config
        return 0
    fi
    
    # Get Ollama user info from /etc/passwd
    local ollama_uid=""
    local ollama_gid=""
    local ollama_home=""
    
    if id ollama &>/dev/null; then
        ollama_uid=$(id -u ollama)
        ollama_gid=$(id -g ollama)
        ollama_home=$(getent passwd ollama | cut -d: -f6)
        log_info "Ollama user: UID=$ollama_uid, GID=$ollama_gid, HOME=$ollama_home"
    else
        log_error "Ollama user not found in /etc/passwd"
        return 1
    fi
    
    # Find all Ollama data locations
    local ollama_locations=(
        "/usr/share/ollama/.ollama"
        "$ollama_home/.ollama"
        "/var/lib/ollama"
        "/root/.ollama"
    )
    
    # Stop Ollama
    safe_stop_service ollama
    
    # Migrate data from each location
    local migrated=false
    
    for src in "${ollama_locations[@]}"; do
        if [ -d "$src" ] && [ "$(ls -A "$src" 2>/dev/null)" ]; then
            log_info "Found Ollama data at: $src"
            log_info "Size: $(get_dir_size "$src")"
            
            echo "Contents:"
            ls -la "$src/" | head -10
            echo
            
            log_info "Migrating to $OLLAMA_NEW_HOME..."
            
            # Use rsync for reliable copy with progress
            rsync -av --progress "$src/" "$OLLAMA_NEW_HOME/"
            
            log_success "Migrated data from $src"
            migrated=true
            
            # Rename old directory as backup
            mv "$src" "${src}.migrated.$(date +%Y%m%d%H%M%S)"
            log_info "Old location backed up"
        fi
    done
    
    if [ "$migrated" = false ]; then
        log_info "No existing Ollama data found to migrate"
    fi
    
    # Set correct ownership (from /etc/passwd)
    log_info "Setting ownership to ollama:ollama (UID:$ollama_uid, GID:$ollama_gid)..."
    chown -R "$ollama_uid:$ollama_gid" "$OLLAMA_NEW_HOME"
    chmod -R u+rwX,go+rX "$OLLAMA_NEW_HOME"
    
    log_success "Ownership set correctly"
    
    # Create systemd override
    create_ollama_config
    
    # Start and verify
    safe_start_service ollama
    
    # Verify models are accessible
    sleep 3
    log_info "Verifying Ollama can see models..."
    if ollama list &>/dev/null; then
        ollama list
        log_success "Ollama migration complete"
    else
        log_warn "Ollama list failed, but service is running"
    fi
}

create_ollama_config() {
    log_info "Creating Ollama systemd override..."
    
    local override_dir="/etc/systemd/system/ollama.service.d"
    local override_file="$override_dir/override.conf"
    
    mkdir -p "$override_dir"
    
    cat > "$override_file" << EOF
# Ollama configuration - use /data partition
[Service]
# Listen on all interfaces
Environment="OLLAMA_HOST=0.0.0.0"

# Store models on data partition
Environment="OLLAMA_MODELS=$OLLAMA_NEW_HOME/models"

# Set home directory
Environment="HOME=$OLLAMA_NEW_HOME"
EOF
    
    log_success "Created $override_file"
    cat "$override_file"
    
    # Also create environment file for shell access
    cat > /etc/profile.d/ollama.sh << EOF
# Ollama environment
export OLLAMA_HOST=0.0.0.0
export OLLAMA_MODELS=$OLLAMA_NEW_HOME/models
EOF
    
    log_success "Created /etc/profile.d/ollama.sh"
    
    systemctl daemon-reload
}

#===============================================================================
# STEP 6: MIGRATE DOCKER
#===============================================================================

migrate_docker() {
    log_section "STEP 6: MIGRATE DOCKER DATA"
    
    if ! command -v docker &>/dev/null; then
        log_warn "Docker not installed, skipping migration"
        log_info "Will configure for future installation"
        create_docker_config
        return 0
    fi
    
    local docker_old="/var/lib/docker"
    
    # Check current Docker root
    local current_root=$(docker info 2>/dev/null | grep "Docker Root Dir" | awk '{print $4}')
    log_info "Current Docker Root: ${current_root:-$docker_old}"
    
    # Check for data
    if [ -d "$docker_old" ] && [ "$(ls -A "$docker_old" 2>/dev/null)" ]; then
        log_info "Docker data size: $(get_dir_size "$docker_old")"
        
        echo "Docker storage breakdown:"
        for subdir in overlay2 image containers volumes buildkit; do
            if [ -d "$docker_old/$subdir" ]; then
                echo "  $subdir: $(get_dir_size "$docker_old/$subdir")"
            fi
        done
        echo
    else
        log_info "No existing Docker data to migrate"
    fi
    
    # Stop all Docker services completely
    log_info "Stopping Docker services..."
    safe_stop_service docker.socket
    safe_stop_service docker
    safe_stop_service containerd
    
    # Wait for complete shutdown
    sleep 3
    
    # Kill any remaining Docker processes
    pkill -9 dockerd 2>/dev/null || true
    pkill -9 containerd 2>/dev/null || true
    sleep 2
    
    # Verify stopped
    if pgrep -x dockerd &>/dev/null; then
        log_error "Docker still running, cannot migrate"
        return 1
    fi
    log_success "Docker completely stopped"
    
    # Migrate data if exists
    if [ -d "$docker_old" ] && [ "$(ls -A "$docker_old" 2>/dev/null)" ]; then
        log_info "Migrating Docker data to $DOCKER_NEW_HOME..."
        log_warn "This may take a while for large installations..."
        
        # Use rsync for reliable copy
        rsync -av --progress "$docker_old/" "$DOCKER_NEW_HOME/"
        
        log_success "Docker data migrated"
        
        # Backup old location
        mv "$docker_old" "${docker_old}.migrated.$(date +%Y%m%d%H%M%S)"
        log_info "Old Docker data backed up"
    fi
    
    # Create Docker config
    create_docker_config
    
    # Start Docker
    log_info "Starting Docker services..."
    systemctl start containerd
    sleep 2
    systemctl start docker
    sleep 3
    
    # Verify
    if systemctl is-active --quiet docker; then
        log_success "Docker is running"
        
        local new_root=$(docker info 2>/dev/null | grep "Docker Root Dir" | awk '{print $4}')
        log_info "Docker Root Dir: $new_root"
        
        if [ "$new_root" = "$DOCKER_NEW_HOME" ]; then
            log_success "Docker correctly using new location"
        else
            log_error "Docker not using new location!"
            log_error "Expected: $DOCKER_NEW_HOME"
            log_error "Actual: $new_root"
        fi
        
        # Show Docker info
        docker info 2>/dev/null | grep -E "(Root Dir|Storage Driver|Containers|Images)"
    else
        log_error "Docker failed to start"
        journalctl -u docker --no-pager -n 20
    fi
}

create_docker_config() {
    log_info "Creating Docker daemon configuration..."
    
    mkdir -p /etc/docker
    
    # Backup existing config
    if [ -f /etc/docker/daemon.json ]; then
        cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%Y%m%d%H%M%S)
    fi
    
    cat > /etc/docker/daemon.json << EOF
{
  "data-root": "$DOCKER_NEW_HOME",
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "live-restore": true
}
EOF
    
    log_success "Created /etc/docker/daemon.json"
    cat /etc/docker/daemon.json
}

#===============================================================================
# STEP 7: CONFIGURE GIT
#===============================================================================

configure_git() {
    log_section "STEP 7: CONFIGURE GIT"
    
    log_info "Setting up Git to use data partition..."
    
    # Create Git LFS storage
    mkdir -p "$GIT_NEW_HOME/lfs"
    chmod 755 "$GIT_NEW_HOME/lfs"
    
    # Create global gitconfig for git lfs
    cat > /etc/gitconfig << EOF
[lfs]
    storage = $GIT_NEW_HOME/lfs

[safe]
    directory = *
EOF
    
    log_success "Created /etc/gitconfig"
    
    # Create environment file for Git
    cat > /etc/profile.d/git-data.sh << EOF
# Git configuration - use data partition
export GIT_LFS_STORAGE=$GIT_NEW_HOME/lfs

# For large repos, clone to /data/git/repos
# git clone <url> $GIT_NEW_HOME/repos/<name>
EOF
    
    chmod 644 /etc/profile.d/git-data.sh
    log_success "Created /etc/profile.d/git-data.sh"
    
    # If any user has git configured, update their config
    for user_home in /home/* /root; do
        if [ -f "$user_home/.gitconfig" ]; then
            log_info "Found git config in $user_home"
            
            # Add LFS storage setting if not present
            if ! grep -q "lfs" "$user_home/.gitconfig" 2>/dev/null; then
                cat >> "$user_home/.gitconfig" << EOF

[lfs]
    storage = $GIT_NEW_HOME/lfs
EOF
                log_success "Updated $user_home/.gitconfig"
            fi
        fi
    done
    
    log_info "Git directories:"
    echo "  Repos:    $GIT_NEW_HOME/repos"
    echo "  LFS:      $GIT_NEW_HOME/lfs"
    
    log_success "Git configured"
}

#===============================================================================
# STEP 8: CLEANUP AND VERIFY
#===============================================================================

cleanup_and_verify() {
    log_section "STEP 8: VERIFICATION AND CLEANUP"
    
    # Verify mount
    log_info "Verifying mount..."
    if mountpoint -q "$MOUNT_POINT"; then
        log_success "$MOUNT_POINT is mounted"
        df -h "$MOUNT_POINT"
    else
        log_error "$MOUNT_POINT is not mounted!"
    fi
    echo
    
    # Verify fstab
    log_info "Verifying fstab..."
    if grep -q "$MOUNT_POINT" /etc/fstab; then
        log_success "fstab entry present"
        grep "$MOUNT_POINT" /etc/fstab
    else
        log_error "fstab entry missing!"
    fi
    echo
    
    # Verify Ollama
    log_info "Verifying Ollama..."
    if command -v ollama &>/dev/null; then
        if systemctl is-active --quiet ollama; then
            log_success "Ollama service: running"
            log_info "Models directory: $OLLAMA_NEW_HOME/models"
            ls -la "$OLLAMA_NEW_HOME/models/" 2>/dev/null | head -5 || echo "  (empty)"
        else
            log_warn "Ollama service: not running"
        fi
    else
        log_info "Ollama: not installed"
    fi
    echo
    
    # Verify Docker
    log_info "Verifying Docker..."
    if command -v docker &>/dev/null; then
        if systemctl is-active --quiet docker; then
            log_success "Docker service: running"
            docker info 2>/dev/null | grep "Docker Root Dir" || true
        else
            log_warn "Docker service: not running"
        fi
    else
        log_info "Docker: not installed"
    fi
    echo
    
    # Show disk usage
    log_info "Final disk usage:"
    echo
    echo "Root filesystem:"
    df -h /
    echo
    echo "Data partition:"
    df -h "$MOUNT_POINT"
    echo
    echo "Data breakdown:"
    du -sh "$MOUNT_POINT"/* 2>/dev/null || echo "  (empty)"
    echo
    
    # Cleanup recommendations
    log_info "CLEANUP RECOMMENDATIONS:"
    echo
    echo "After verifying everything works, remove old data to free root partition:"
    echo
    
    # Find migrated directories
    for dir in /usr/share/ollama/.ollama.migrated.* /var/lib/docker.migrated.* /home/*/.ollama.migrated.* /root/.ollama.migrated.*; do
        if [ -d "$dir" ] 2>/dev/null; then
            echo "  rm -rf $dir"
        fi
    done
    
    echo
    echo "To verify models after cleanup:"
    echo "  ollama list"
    echo "  ollama pull llama3.2:latest"
    echo "  ls -la $OLLAMA_NEW_HOME/models/"
    echo
}

#===============================================================================
# FINAL SUMMARY
#===============================================================================

show_summary() {
    log_section "SETUP COMPLETE"
    
    echo "STORAGE CONFIGURATION:"
    echo "─────────────────────────────────────────────────────────────────────"
    echo "  Mount Point:     $MOUNT_POINT"
    echo "  LVM:             /dev/$VG_NAME/$LV_NAME"
    echo "  Filesystem:      XFS"
    echo
    
    echo "DATA LOCATIONS:"
    echo "─────────────────────────────────────────────────────────────────────"
    echo "  Ollama Models:   $OLLAMA_NEW_HOME/models"
    echo "  Docker Data:     $DOCKER_NEW_HOME"
    echo "  Git LFS:         $GIT_NEW_HOME/lfs"
    echo "  Git Repos:       $GIT_NEW_HOME/repos"
    echo
    
    echo "SERVICE STATUS:"
    echo "─────────────────────────────────────────────────────────────────────"
    echo -n "  Ollama:     "
    systemctl is-active ollama 2>/dev/null || echo "not installed"
    echo -n "  Docker:     "
    systemctl is-active docker 2>/dev/null || echo "not installed"
    echo -n "  Containerd: "
    systemctl is-active containerd 2>/dev/null || echo "not installed"
    echo
    
    echo "CONFIGURATION FILES CREATED:"
    echo "─────────────────────────────────────────────────────────────────────"
    echo "  /etc/systemd/system/ollama.service.d/override.conf"
    echo "  /etc/docker/daemon.json"
    echo "  /etc/profile.d/ollama.sh"
    echo "  /etc/profile.d/git-data.sh"
    echo "  /etc/gitconfig"
    echo
    
    echo "DISK USAGE:"
    echo "─────────────────────────────────────────────────────────────────────"
    df -h / "$MOUNT_POINT" 2>/dev/null
    echo
    
    log_success "All done! Your system is now configured to use $MOUNT_POINT for data storage."
}

#===============================================================================
# MAIN
#===============================================================================

main() {
    echo
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}     COMPLETE STORAGE SETUP AND DATA MIGRATION${NC}"
    echo -e "${GREEN}     For CentOS Stream 9 / RHEL 9${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo
    
    preflight_checks
    
    echo
    log_warn "This script will:"
    echo "  1. Set up LVM on $DATA_PARTITION"
    echo "  2. Create and mount $MOUNT_POINT filesystem"
    echo "  3. Migrate all Ollama data"
    echo "  4. Migrate all Docker data"
    echo "  5. Configure Git to use data partition"
    echo "  6. Update all service configurations"
    echo
    
    read -p "Proceed with setup? [y/N] " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_error "Aborted by user"
        exit 0
    fi
    
    # Execute all steps
    fix_lvm_devices_file || true  # Continue even if this fails
    setup_lvm
    format_and_mount
    create_directories
    migrate_ollama
    migrate_docker
    configure_git
    cleanup_and_verify
    show_summary
}

# Run main
main "$@"
