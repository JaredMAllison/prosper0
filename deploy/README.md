# Layer 6: Portable Deployment

The deployment layer is configurable. Vault and model weights can live on the host, on a USB drive, or split. Size is tracked and optimized as a project statistic, not fixed to a hard limit.

## The Reference Deployment

The portfolio showcase configuration: everything on a USB drive, hardware-paired, launched from a desktop shortcut.

Setup story: hand someone the drive. Ask, "can I make a shortcut on your desktop?" That's it.

## Deployment Configurations

| Config | Vault | Model | Notes |
|---|---|---|---|
| USB-first | On drive | On drive | Maximum portability |
| Host-first | On host | On host | Best inference performance |
| Hybrid | On drive | On host (RAM) | Vault portable; model pre-loaded |
| Custom | Operator-defined | Operator-defined | Document trade-offs |

## Files

```
deploy/
├── docker-compose.yml  ← configurable volume paths
├── launch.sh           ← unlock → mount → start container → open interface
├── stop.sh             ← graceful shutdown → lock partition
├── udev/               ← removal detection rule + stop script
└── pairing/            ← hardware-drive pairing setup and re-pairing docs
```

## On Physical Removal

A udev rule fires a stop script on device removal — but the kernel drops the block device the moment the drive is yanked. Containers will encounter I/O errors and crash rather than shut down gracefully. The LUKS target disappears with the block device.

**What is guaranteed:** no vault data ends up on the host. The data was on the drive; you pulled the drive; the data left with you. That's the actual security property.

**What is best-effort:** the udev script attempts to terminate containers and sync pending writes before the device disappears. In practice, a yank is ungraceful. The startup script handles the dirty container state on next use.

The graceful path is `stop.sh` (launcher close). The physical-pull path gets you to the same end state — data with you, host clean — through a messier route.
