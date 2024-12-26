# HomeLab journey
## python scripts
### truenas-schedule
This script is used to start/stop a TrueNAS system via Wake-On-LAN and the TrueNAS API.
It wakes the system and waits for any number of tasks to be completed + some additional time before shutting it down again.
The script is intended to be run as a cron job on some other system (e.g. a Pi):
For me, my data protection tasks are scheduled to run at 12am, so I have the Pi wake the TrueNAS system at 11:45pm and shut it down after 30min of idle:
```bash
45 23 * * * truenas-schedule --ip <TRUENAS_IP> --mac <TRUENAS_MAC> --api-key <API_KEY> --interval 60 --threshold 1800 --log /home/pi/truenas.log
```
## Plans

- power efficient home server
- remote access
- local backup
 - RAW photos (Lightroom interface/plugin?)
 - video surveillance
   - [Agent DVR](https://www.ispyconnect.com/docs/agent/about)

## Subprojects
- [record player](recordplayer.md)
