# Fixed stop() method for ProgramRunner class
# Replace the existing stop() method with this

def stop(self, timeout: float = 5.0):
    """
    Stop the running program and all child processes.
    
    Args:
        timeout: Seconds to wait for graceful shutdown
    """
    if not self.running:
        self.logger.info("Stop called but program not running")
        return
    
    self.logger.info("Stopping program...")
    self.running = False
    
    if self.process:
        try:
            pid = self.process.pid
            pgid = os.getpgid(pid)
            
            self.logger.info(f"Stopping process: PID={pid}, PGID={pgid}")
            
            # Get all processes in the target group
            import subprocess
            try:
                result = subprocess.run(
                    ['ps', '-g', str(pgid), '-o', 'pid', '--no-headers'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    pids_in_group = [int(p.strip()) for p in result.stdout.strip().split('\n') if p.strip()]
                    self.logger.info(f"Found {len(pids_in_group)} processes in group {pgid}")
                    
                    # Kill each process individually, skipping our own and parent
                    killed_count = 0
                    for proc_pid in pids_in_group:
                        if proc_pid == self.baseline.own_pid:
                            self.logger.info(f"Skipping own PID {proc_pid}")
                            continue
                        if proc_pid == self.baseline.parent_pid:
                            self.logger.info(f"Skipping parent PID {proc_pid}")
                            continue
                        
                        try:
                            # Try SIGTERM first
                            os.kill(proc_pid, signal.SIGTERM)
                            self.logger.info(f"Sent SIGTERM to {proc_pid}")
                            killed_count += 1
                        except ProcessLookupError:
                            self.logger.debug(f"Process {proc_pid} already dead")
                        except Exception as e:
                            self.logger.warning(f"Error killing {proc_pid}: {e}")
                    
                    self.logger.info(f"Sent SIGTERM to {killed_count} processes")
                    
                    # Wait a bit for graceful shutdown
                    time.sleep(1)
                    
                    # Force kill any remaining processes
                    for proc_pid in pids_in_group:
                        if proc_pid == self.baseline.own_pid or proc_pid == self.baseline.parent_pid:
                            continue
                        
                        try:
                            # Check if still alive
                            os.kill(proc_pid, 0)
                            # Still alive, force kill
                            os.kill(proc_pid, signal.SIGKILL)
                            self.logger.info(f"Sent SIGKILL to {proc_pid}")
                        except ProcessLookupError:
                            # Already dead, good
                            pass
                        except Exception as e:
                            self.logger.warning(f"Error force killing {proc_pid}: {e}")
                    
            except Exception as e:
                self.logger.warning(f"Error getting process group: {e}")
                # Fallback: just kill the main process
                try:
                    os.kill(pid, signal.SIGKILL)
                    self.logger.info(f"Killed main process {pid}")
                except:
                    pass
            
            # Wait for process to die
            try:
                self.process.wait(timeout=timeout)
                self.logger.info("Process terminated")
            except subprocess.TimeoutExpired:
                self.logger.warning("Process did not terminate, may still be running")
            except:
                pass
                
        except Exception as e:
            self.logger.error(f"Error stopping program: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
        finally:
            self.process = None