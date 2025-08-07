
Tezos Baker Monitor
===================

This project monitors Tezos delegates for baking and attestation activity, stores results in a database, and sends alerts if thresholds are exceeded. Alerts can be sent to the console, AWS CloudWatch, and/or Telegram.

Features
--------
- Monitors baking and attestation rights for configured delegates
- Stores block-level and attestation results in a database (SQLite)
- Configurable alert thresholds and monitoring windows
- Sends alerts to console, AWS CloudWatch, and/or Telegram

Setup
-----
1. Clone the repository, setup a virtual Python environmetn, and install dependencies:
   ```bash
   python3 -m venv myenv
   source myenv/bin/activate
   python3 -m pip install -r requirements.txt
   ```

2. Configure your `.env` file with the following variables:
   - `RPC_URL` - Tezos node RPC endpoint
   - `DELEGATES_TO_MONITOR_PARAMETER` - Json file containting the list of delegates to monitor
   - `BLOCK_SLIDING_WINDOW_SIZE` - Number of blocks to look back
   - `ALERT_BAKING_THRESHOLD` - Missed baking threshold
   - `ALERT_BAKING_BLOCK_WINDOW` - Block window for baking alerts
   - `ALERT_ATTESTATION_THRESHOLD` - Missed attestation threshold
   - `ALERT_ATTESTATION_BLOCK_WINDOW` - Block window for attestation alerts
   - (Optional) `SEND_ALERT_TO_CLOUDWATCH=true`, `CLOUDWATCH_LOG_GROUP=YourLogGroup`, `CLOUDWATCH_STREAM_NAME=alerts` for AWS CloudWatch alerts
   - (Optional) `SEND_ALERT_TO_TELEGRAM=true`, `TELEGRAM_BOT_TOKEN=...`, `TELEGRAM_CHAT_ID=...` for Telegram alerts

3. (Optional) For AWS CloudWatch alerts
   - install boto3:
   ```bash
   pip install boto3
   ```
   
   - Configure AWS or assign policy to EC2 instance

4. (Optional) For Telegram alerts, create a bot and get your chat ID.

Running
-------
Run the monitor with:
```bash
python3 main.py
```

The script will:
- Monitor delegates for missed bakings and attestations
- Store results in the database
- Send alerts if thresholds are exceeded. Send recovery alert, if a baker successfully bakes again a block after an baking alert was triggered.

The script should be executed regularly to remain in sync with the blockchain status.
Thus, consider adding a cron job. For instance, a cron job running every minute:
```bash
* * * * * cd /home/ec2-user/ghost/tezos-baker-monitor/ && /home/ec2-user/ghost/tezos-baker-monitor/myenv/bin/python3 /home/ec2-user/ghost/tezos-baker-monitor/main.py >> /home/ec2-user/cron-ghost.log 2>&1
```

Consider regularly backing up or deleting log data.
For example, you can implement a cron job to move the log file once a week:
```bash
0 3 * * 0 mv /home/ec2-user/cron-ghost.log /home/ec2-user/cron-ghost_old.log
```
This ensures that at least one week of log data is always retained.

Database
--------
By default, uses SQLite (`state.db`). You can switch to PostgreSQL by changing the `db_url` in `main.py`.

Customization
-------------
- Adjust thresholds and windows in your `.env` file
- Extend alerting logic in `alerting/alert_manager.py`

---
For more details, see the code and comments in each module.

Telegram setup / configuration
------------------------------
1. Create new bot with BotFather `/newbot`
2. Extract botId token
3. Create group in Telegram
4. Add the bot to the group
5. Change the bot's group policy to allow accessing message in the group chat. 
6. Send message in group
7. Call `https://api.telegram.org/bot<token>/getUpdates` and extract chat id (chat_id is an ID with 9-10 decimals)
8. Change the bot's group policy to disallow accessing message in the group chat. 
