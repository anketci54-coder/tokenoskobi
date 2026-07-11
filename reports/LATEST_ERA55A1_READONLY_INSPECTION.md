# ERA55A_1 READ-ONLY INSPECTION REPORT

UTC: `2026-07-11T06:15:55.480509+00:00`

Result: `WARN_P0_FINDINGS_RECORDED_READONLY`

ERA55 status: `OPEN`

Live runtime/DB/service/timer/panel mutation: `false`

## Systemd and Timer

```json
{
  "service": {
    "unit": "tokenoskobi-news-radar-refresh.service",
    "values": {
      "Type": "oneshot",
      "Restart": "no",
      "RestartUSec": "100ms",
      "TimeoutStartUSec": "1min 10s",
      "TimeoutStopUSec": "1min 30s",
      "RuntimeMaxUSec": "infinity",
      "MainPID": "0",
      "Result": "success",
      "NRestarts": "0",
      "ExecMainStartTimestamp": "Sat 2026-07-11 09:14:49 EEST",
      "ExecMainStartTimestampMonotonic": "6268358919751",
      "ExecMainExitTimestamp": "Sat 2026-07-11 09:14:50 EEST",
      "ExecMainExitTimestampMonotonic": "6268359645905",
      "ExecMainStatus": "0",
      "ExecStart": "{ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py ; ignore_errors=no ; start_time=[Sat 2026-07-11 09:14:49 EEST] ; stop_time=[Sat 2026-07-11 09:14:50 EEST] ; pid=3425826 ; code=exited ; status=0 }",
      "KillMode": "control-group",
      "LoadState": "loaded",
      "ActiveState": "inactive",
      "SubState": "dead",
      "FragmentPath": "/etc/systemd/system/tokenoskobi-news-radar-refresh.service",
      "UnitFileState": "static"
    },
    "command": {
      "cmd": [
        "systemctl",
        "show",
        "tokenoskobi-news-radar-refresh.service",
        "--no-pager",
        "--property=LoadState,ActiveState,SubState,UnitFileState,FragmentPath,Type,ExecStart,ExecMainStartTimestamp,ExecMainExitTimestamp,ExecMainStartTimestampMonotonic,ExecMainExitTimestampMonotonic,ExecMainStatus,Result,TimeoutStartUSec,TimeoutStopUSec,RuntimeMaxUSec,Restart,RestartUSec,KillMode,MainPID,NRestarts"
      ],
      "rc": 0,
      "stdout": "Type=oneshot\nRestart=no\nRestartUSec=100ms\nTimeoutStartUSec=1min 10s\nTimeoutStopUSec=1min 30s\nRuntimeMaxUSec=infinity\nMainPID=0\nResult=success\nNRestarts=0\nExecMainStartTimestamp=Sat 2026-07-11 09:14:49 EEST\nExecMainStartTimestampMonotonic=6268358919751\nExecMainExitTimestamp=Sat 2026-07-11 09:14:50 EEST\nExecMainExitTimestampMonotonic=6268359645905\nExecMainStatus=0\nExecStart={ path=/usr/bin/python3 ; argv[]=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py ; ignore_errors=no ; start_time=[Sat 2026-07-11 09:14:49 EEST] ; stop_time=[Sat 2026-07-11 09:14:50 EEST] ; pid=3425826 ; code=exited ; status=0 }\nKillMode=control-group\nLoadState=loaded\nActiveState=inactive\nSubState=dead\nFragmentPath=/etc/systemd/system/tokenoskobi-news-radar-refresh.service\nUnitFileState=static",
      "stderr": ""
    }
  },
  "timer": {
    "unit": "tokenoskobi-news-radar-refresh.timer",
    "values": {
      "Unit": "tokenoskobi-news-radar-refresh.service",
      "NextElapseUSecRealtime": "",
      "LastTriggerUSec": "Sat 2026-07-11 09:14:49 EEST",
      "Result": "success",
      "AccuracyUSec": "30s",
      "RandomizedDelayUSec": "0",
      "Persistent": "no",
      "LoadState": "loaded",
      "ActiveState": "active",
      "SubState": "waiting",
      "FragmentPath": "/etc/systemd/system/tokenoskobi-news-radar-refresh.timer",
      "UnitFileState": "enabled"
    },
    "command": {
      "cmd": [
        "systemctl",
        "show",
        "tokenoskobi-news-radar-refresh.timer",
        "--no-pager",
        "--property=LoadState,ActiveState,SubState,UnitFileState,FragmentPath,Unit,OnBootUSec,OnUnitActiveUSec,OnActiveUSec,AccuracyUSec,RandomizedDelayUSec,Persistent,LastTriggerUSec,NextElapseUSecRealtime,Result"
      ],
      "rc": 0,
      "stdout": "Unit=tokenoskobi-news-radar-refresh.service\nNextElapseUSecRealtime=\nLastTriggerUSec=Sat 2026-07-11 09:14:49 EEST\nResult=success\nAccuracyUSec=30s\nRandomizedDelayUSec=0\nPersistent=no\nLoadState=loaded\nActiveState=active\nSubState=waiting\nFragmentPath=/etc/systemd/system/tokenoskobi-news-radar-refresh.timer\nUnitFileState=enabled",
      "stderr": ""
    }
  },
  "service_unit_text": {
    "cmd": [
      "systemctl",
      "cat",
      "tokenoskobi-news-radar-refresh.service",
      "--no-pager"
    ],
    "rc": 0,
    "stdout": "# /etc/systemd/system/tokenoskobi-news-radar-refresh.service\n[Unit]\nDescription=Tokenoskobi News Radar Refresh Runner\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nType=oneshot\nUser=root\nWorkingDirectory=/root/tokenoskobi_clean_v1\nExecStart=/usr/bin/python3 /root/tokenoskobi_clean_v1/tools/news_radar_refresh_runner_v1.py\nTimeoutStartSec=70\nNice=5\nIOSchedulingClass=best-effort\nStandardOutput=append:/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.log\nStandardError=append:/root/tokenoskobi_clean_v1/logs/news_radar/news_radar_refresh.err.log",
    "stderr": ""
  },
  "timer_unit_text": {
    "cmd": [
      "systemctl",
      "cat",
      "tokenoskobi-news-radar-refresh.timer",
      "--no-pager"
    ],
    "rc": 0,
    "stdout": "# /etc/systemd/system/tokenoskobi-news-radar-refresh.timer\n[Unit]\nDescription=Run Tokenoskobi News Radar Refresh every 20 minutes\n\n[Timer]\nOnActiveSec=20min\nOnUnitActiveSec=20min\nAccuracySec=30s\nRandomizedDelaySec=0\nPersistent=false\nUnit=tokenoskobi-news-radar-refresh.service\n\n[Install]\nWantedBy=timers.target",
    "stderr": ""
  },
  "list_timers": {
    "cmd": [
      "systemctl",
      "list-timers",
      "--all",
      "tokenoskobi-news-radar-refresh.timer",
      "--no-pager"
    ],
    "rc": 0,
    "stdout": "NEXT                          LEFT LAST                              PASSED UNIT                                 ACTIVATES\nSat 2026-07-11 09:34:49 EEST 18min Sat 2026-07-11 09:14:49 EEST 1min 5s ago tokenoskobi-news-radar-refresh.timer tokenoskobi-news-radar-refresh.service\n\n1 timers listed.",
    "stderr": ""
  },
  "journal_last_24h": {
    "cmd": [
      "journalctl",
      "-u",
      "tokenoskobi-news-radar-refresh.service",
      "--since",
      "24 hours ago",
      "--no-pager",
      "-n",
      "300",
      "-o",
      "short-iso"
    ],
    "rc": 0,
    "stdout": "2026-07-10T09:31:43+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T09:31:43+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T09:31:43+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T09:51:44+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T09:51:44+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T09:51:44+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T10:11:46+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T10:11:46+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T10:11:46+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T10:31:46+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T10:31:47+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T10:31:47+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T10:51:54+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T10:51:55+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T10:51:55+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T11:11:57+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T11:11:58+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T11:11:58+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T11:32:01+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T11:32:01+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T11:32:01+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T11:52:01+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T11:52:02+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T11:52:02+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T12:12:09+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T12:12:10+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T12:12:10+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T12:32:11+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T12:32:12+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T12:32:12+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T12:52:11+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T12:52:12+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T12:52:12+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T13:12:13+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T13:12:13+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T13:12:13+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T13:32:14+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T13:32:15+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T13:32:15+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T13:52:17+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T13:52:18+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T13:52:18+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T14:12:17+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T14:12:18+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T14:12:18+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T14:32:19+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T14:32:20+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T14:32:20+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T14:52:20+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T14:52:21+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T14:52:21+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T15:12:22+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T15:12:23+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T15:12:23+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T15:32:29+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T15:32:30+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T15:32:30+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T15:52:30+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T15:52:31+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T15:52:31+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T16:12:39+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T16:12:40+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T16:12:40+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T16:32:41+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T16:32:42+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T16:32:42+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T16:52:45+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T16:52:46+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T16:52:46+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T17:12:47+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T17:12:48+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T17:12:48+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T17:32:48+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T17:32:49+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T17:32:49+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T17:52:49+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T17:52:50+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T17:52:50+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T18:12:50+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T18:12:50+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T18:12:50+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T18:32:51+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T18:32:52+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T18:32:52+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T18:52:52+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T18:52:53+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T18:52:53+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T19:12:57+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T19:12:58+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T19:12:58+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T19:32:57+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T19:32:58+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T19:32:58+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T19:52:57+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T19:52:58+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T19:52:58+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T20:12:59+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T20:13:00+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T20:13:00+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T20:33:02+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T20:33:03+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T20:33:03+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T20:53:02+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T20:53:03+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T20:53:03+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T21:13:07+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T21:13:08+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T21:13:08+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T21:33:09+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T21:33:10+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T21:33:10+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T21:53:18+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T21:53:19+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T21:53:19+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T22:13:19+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T22:13:20+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T22:13:20+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T22:33:23+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T22:33:24+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T22:33:24+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T22:53:27+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T22:53:28+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T22:53:28+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T23:13:28+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T23:13:29+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T23:13:29+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T23:33:29+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T23:33:30+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T23:33:30+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-10T23:53:33+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-10T23:53:34+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-10T23:53:34+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T00:13:36+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T00:13:37+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T00:13:37+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T00:33:39+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T00:33:40+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T00:33:40+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T00:53:40+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T00:53:41+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T00:53:41+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T01:13:45+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T01:13:46+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T01:13:46+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T01:33:46+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T01:33:47+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T01:33:47+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T01:53:49+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T01:53:50+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T01:53:50+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T02:13:51+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T02:13:52+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T02:13:52+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T02:33:54+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T02:33:55+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T02:33:55+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T02:53:55+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T02:53:56+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T02:53:56+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T03:13:59+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T03:14:00+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T03:14:00+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T03:34:01+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T03:34:02+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T03:34:02+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T03:54:09+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T03:54:10+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T03:54:10+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T04:14:16+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T04:14:16+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T04:14:16+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T04:34:19+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T04:34:20+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T04:34:20+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T04:54:19+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T04:54:20+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T04:54:20+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T05:14:23+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T05:14:24+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T05:14:24+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T05:34:24+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T05:34:25+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T05:34:25+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T05:54:26+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T05:54:27+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T05:54:27+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T06:14:29+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T06:14:30+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T06:14:30+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T06:34:32+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T06:34:33+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T06:34:33+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T06:54:33+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T06:54:34+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T06:54:34+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T07:14:33+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T07:14:34+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T07:14:34+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T07:34:37+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T07:34:38+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T07:34:38+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T07:54:39+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T07:54:40+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T07:54:40+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T08:14:39+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T08:14:40+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T08:14:40+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T08:34:40+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T08:34:41+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T08:34:41+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T08:54:48+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T08:54:49+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T08:54:49+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.\n2026-07-11T09:14:49+03:00 v2202604354387455154 systemd[1]: Starting tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner...\n2026-07-11T09:14:50+03:00 v2202604354387455154 systemd[1]: tokenoskobi-news-radar-refresh.service: Deactivated successfully.\n2026-07-11T09:14:50+03:00 v2202604354387455154 systemd[1]: Finished tokenoskobi-news-radar-refresh.service - Tokenoskobi News Radar Refresh Runner.",
    "stderr": ""
  },
  "derived": {
    "last_execution_duration_ms": 726.154,
    "timer_cadence_usec": null,
    "timer_safety_margin_ms": null,
    "duration_baseline_complete": true,
    "overlap_risk_status": "NEEDS_GRANULAR_DURATION_BASELINE"
  }
}
```

## SQLite Durability and Integrity

```json
{
  "db_path": "/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite",
  "exists": true,
  "size_bytes": 5857280,
  "mtime_utc": "2026-07-11T04:34:38.166982+00:00",
  "readonly_uri": "file:/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite?mode=ro",
  "query_only": true,
  "total_changes": 0,
  "pragmas": {
    "journal_mode": "delete",
    "synchronous": 2,
    "locking_mode": "normal",
    "foreign_keys": 0,
    "busy_timeout": 20000,
    "cache_size": -2000,
    "temp_store": 0,
    "mmap_size": 0,
    "page_size": 4096,
    "page_count": 1430,
    "freelist_count": 0,
    "query_only": 1
  },
  "integrity_check": "ok",
  "quick_check": "ok",
  "table_counts": {
    "news_raw_feed_events": 390,
    "news_token_match_events": 201,
    "news_signal_events": 201,
    "news_score_events_v1": 201,
    "news_runtime_freshness_v1": 3
  },
  "table_max_timestamps": {
    "news_raw_feed_events": {
      "column": "published_at_utc",
      "max": "2026-07-11T04:12:30+00:00"
    },
    "news_token_match_events": {
      "column": "created_at_utc",
      "max": "2026-07-11T04:34:38.146743+00:00"
    },
    "news_signal_events": {
      "column": "created_at_utc",
      "max": "2026-07-11T04:34:38.146743+00:00"
    },
    "news_score_events_v1": {
      "column": "created_at_utc",
      "max": "2026-07-11T04:34:38.146743+00:00"
    },
    "news_runtime_freshness_v1": {
      "column": "created_at_utc",
      "max": "2026-07-11T04:34:38.096422+00:00"
    }
  }
}
```

## Queue Policy

```json
{
  "path": "tools/hot_intelligence_ingress_gateway_v1.py",
  "exists": true,
  "sha256": "8d4c1cb568ab194dfb010d66859c45aa29fa044aff1518a656a9f78ecc4fb263",
  "size_bytes": 5469,
  "syntax_ok": true,
  "subprocess_calls": [],
  "timeout_literals": [],
  "slice_limits": [
    50,
    24
  ],
  "queue_capacity_detected": 50,
  "selection_policy": "PRIORITY_DESC_THEN_HOT_UID_TOP_50",
  "dedupe_detected": true,
  "drop_ledger_detected": false,
  "silent_truncation_risk": true,
  "silent_drop_compliance": "FAIL_P0",
  "policy_evidence": [
    "items sorted by priority_score descending",
    "hot_uid used as deterministic tie-break",
    "deduplicated list sliced to first 50",
    "no explicit overflow/drop ledger found"
  ]
}
```

Static conclusion: the current gateway deterministically sorts by priority and retains the top 50. No explicit overflow/drop ledger was detected. Until disproved by runtime evidence, this is treated as a P0 silent intelligence-loss risk.

## Runner Static Inspection

```json
{
  "path": "tools/news_radar_refresh_runner_v1.py",
  "exists": true,
  "sha256": "76794993a67cc50f7cd8d3c84fe3cc1a02485eea08688f35a4c7718e81d18500",
  "size_bytes": 1166,
  "syntax_ok": true,
  "subprocess_calls": [
    "subprocess.run([sys.executable, str(ORIGINAL)] + sys.argv[1:])",
    "subprocess.run([sys.executable, str(HELPER), '--db-path', str(DB), '--write', '--stage', 'NEWS_SYSTEMD_TIMER_DERIVED_REFRESH'])",
    "subprocess.run([sys.executable, str(HOT), '--runtime-refresh'], env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})"
  ],
  "timeout_literals": []
}
```

## Panel and Runtime File Visibility

```json
{
  "data/tokenoskobi_clean_v1.sqlite": {
    "exists": true,
    "size_bytes": 5857280,
    "mtime_utc": "2026-07-11T04:34:38.166982+00:00",
    "sha256": "45b177cbb6fee7c9f0513458ce26a0d1067633130ff1a4edba8519320cc9be35"
  },
  "runtime/state/news_coverage_panel_display_v1.json": {
    "exists": true,
    "size_bytes": 35497,
    "mtime_utc": "2026-07-11T06:14:50.303894+00:00",
    "sha256": "ffbe4980ad8ff0a4fac4073a70ab611c6d68c78d00a0c2ba5322ed6d36c485b0"
  },
  "runtime/state/hot_intelligence_ingress_gateway_v1.json": {
    "exists": true,
    "size_bytes": 37998,
    "mtime_utc": "2026-07-11T06:14:50.343896+00:00",
    "sha256": "44315e7206c4cc8f174d526b048db20dfc95005619d705d3d39334ac9d948cf6"
  },
  "runtime/state/news_active_panel_data_bridge_v1.json": {
    "exists": true,
    "size_bytes": 5654,
    "mtime_utc": "2026-07-11T06:14:50.395899+00:00",
    "sha256": "440e50a1c73084aadf123da2bb7a0fcfe476a7dd84acaa96ef4036cfeb035913"
  },
  "active_panel_8096/current/data/news_coverage_panel_display_v1.json": {
    "exists": true,
    "size_bytes": 35497,
    "mtime_utc": "2026-07-11T06:14:50.391899+00:00",
    "sha256": "ffbe4980ad8ff0a4fac4073a70ab611c6d68c78d00a0c2ba5322ed6d36c485b0"
  },
  "active_panel_8096/current/data/hot_intelligence_ingress_gateway_v1.json": {
    "exists": true,
    "size_bytes": 37998,
    "mtime_utc": "2026-07-11T06:14:50.391899+00:00",
    "sha256": "44315e7206c4cc8f174d526b048db20dfc95005619d705d3d39334ac9d948cf6"
  }
}
```

## Red Team Risks

- **P0 QUEUE_OVERFLOW_SILENT_TRUNCATION_RISK** — Queue keeps deterministic top 50 but no overflow/drop ledger was found. Required: Define overflow policy and record every dropped or displaced event before optimization.
- **P1 SQLITE_JOURNAL_MODE_NOT_WAL** — Current journal_mode=delete. Required: Do not change mode yet; test durability and lock behavior on a temp copy first.
- **P1 PANEL_PROPAGATION_LATENCY_NOT_YET_INSTRUMENTED** — Filesystem timestamps provide visibility but not end-to-end propagation latency. Required: ERA55A_2 must add granular read-only stage timestamps.

## Decision

- No watchdog applied.
- No index added.
- No journal mode changed.
- No cache added.
- No queue policy changed.
- No incremental write applied.
- No burst load executed.
- Next: `ERA55A_2_GRANULAR_INSTRUMENTATION_AND_BASELINE_MEASUREMENT_PLAN`.
