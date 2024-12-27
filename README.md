# HomeLab journey
## python scripts
### truenas-schedule
This script is used to start/stop a TrueNAS system via Wake-On-LAN and the TrueNAS API.
It wakes the system and waits for any number of tasks to be completed + some additional time before shutting it down again.
The script is intended to be run as a cron job on some other system (e.g. a Pi):
For me, my data protection tasks are scheduled to run at 12am, so I have the Pi wake the TrueNAS system at 11:50pm and shut it down after 30min of idle. I installed the package as a tool using [uv](https://github.com/astral-sh/uv) for the <USER> account on the Pi. So the cron job looks like this:
```bash
50 23 * * * <USER> /home/<USER>/.local/bin/uv tool run --from homelab truenas-schedule --log /home/<USER>/truenas_primary.log --ip "<TRUENAS_IP>" --mac "<TRUENAS_MAC>" --api-key "<API_KEY>" --interval 60 --threshold 1800
```
## Plans

- power efficient home server
- remote access
  - [netbird]
(https://github.com/netbirdio/netbird)
    - good overview on overlay VPN by [lawrence systens](https://youtu.be/eCXl09h7lqo)
  - remote backup box (family/friends)
  - cloud backup (hetzner storagebox)
- local backup
 - RAW photos (Lightroom interface/plugin?)
 - video surveillance
   - [Agent DVR](https://www.ispyconnect.com/docs/agent/about)

## Subprojects
- [record player](recordplayer.md)
