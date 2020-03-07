# Systems deployed to server gjl-mini

## Deploy

Connect to AWS server (99.80.106.17) to use path */home/ec2-user/source/gjl_freezer/deploy* where we git clone repository *git@github.com:grey-juice-lab/gjl_freezer.git*

### System files
We can use ansible to deploy files to run python scripts.
```shell script
$ git pull
$ cd deploy
$ ansible-playbook -i inventory install_files.yml --become
```
Dry-run
```shell script
$ git pull
$ cd deploy
$ ansible-playbook -i inventory install_files.yml --become --check
```

We don't need different credentials because we will use freezer's

## Systemd - Unit files

```shell script
# systemctl cat gjl-transporter

[Unit]
Description=Runs gjl-transporter to move files
Wants=gjl-transporter.timer

[Service]
Type=simple
User=greyjuicelab
EnvironmentFile=/etc/profile.d/freezer_envvars.sh
#fix paths
WorkingDirectory=/home/greyjuicelab/source/Transporter/python
ExecStart=/home/greyjuicelab/source/Transporter/python/.venv/bin/python3 Transporter.py rules

[Install]
WantedBy=multi-user.target

```


```shell script
[Unit]
Description=Run Transporter at 00:00 and at 12:00
Requires=gjl-transporter.service

[Timer]
Unit=gjl-transporter.service
OnCalendar=0,12:00:00

[Install]
WantedBy=timers.target

```


