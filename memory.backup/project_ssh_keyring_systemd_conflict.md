---
name: ssh-keyring-systemd-vs-hyprland-conflict
description: "gnome-keyring-daemon's systemd user unit starts WITHOUT ssh+gpg components, racing Hyprland's autostart that has them; result is broken SSH_AUTH_SOCK pointing to non-existent socket"
metadata: 
  node_type: memory
  type: project
  originSessionId: cde2db64-4da3-4d80-aeb6-00c06bcca15a
---

**Symptom:** `ssh-add` fails with "Error connecting to agent: No such file
or directory" even though `SSH_AUTH_SOCK` is set. Git push to SSH remotes
fails with "Permission denied (publickey)".

**Root cause (diagnosed 2026-05-12 on Caramel's Arch+Hyprland machine):**

Three things race at session start:

1. **systemd user unit** `/usr/lib/systemd/user/gnome-keyring-daemon.service`
   has `ExecStart=/usr/bin/gnome-keyring-daemon --foreground --components="pkcs11,secrets"`
   — note **no `ssh` and no `gpg` components**.
2. **Hyprland autostart** `~/.config/hypr/modules/autostart.conf` runs
   `gnome-keyring-daemon --start --components=pkcs11,secrets,ssh,gpg`
   AFTER systemd already launched it — so the autostart's command does nothing
   (daemon already running).
3. **Hyprland environment.conf** exports `SSH_AUTH_SOCK=$XDG_RUNTIME_DIR/keyring/ssh`
   — pointing at the socket the daemon SHOULD have created if ssh component
   were enabled. systemd wins; ssh socket doesn't exist; env var is dangling.

**Immediate fix (one terminal session):**

```bash
pkill -f gnome-keyring-daemon
gnome-keyring-daemon --start --components=pkcs11,secrets,ssh,gpg
ssh-add ~/.ssh/id_ed25519
```

**Permanent fix (so it doesn't recur on next login):**

Disable the systemd user unit since Hyprland autostart is the intended
launcher and currently can't win the race:

```bash
systemctl --user disable --now gnome-keyring-daemon.service gnome-keyring-daemon.socket
```

After this, only Hyprland's autostart.conf starts the daemon, with all
components correctly enabled.

**How to apply when this surfaces again:**
- First check: `pgrep -a gnome-keyring-daemon` — look at the `--components`
  list in the args. If missing `ssh`, you've hit this conflict.
- Apply immediate fix → confirm `ls /run/user/1000/keyring/` now shows
  `ssh` socket → `ssh-add` will work.
- If recurring across reboots, apply permanent fix.

**Why Arch's default gnome-keyring systemd unit is incomplete:** upstream
gnome-keyring ships the systemd unit with abbreviated components. Hyprland
users need the autostart override (or systemctl --user disable) to get
full functionality. Not Hyprland-specific; affects any DE that doesn't
manage gnome-keyring itself.

Established 2026-05-12 after Caramel's `git push` failed mid-workspace-sync.
