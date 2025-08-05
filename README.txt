
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
   - `DELEGATES_TO_MONITOR_PARAMETER` - Comma-separated list of delegates to monitor
   - `BLOCK_SLIDING_WINDOW_SIZE` - Number of blocks to look back
   - `ALERT_BAKING_THRESHOLD` - Missed baking threshold
   - `ALERT_BAKING_BLOCK_WINDOW` - Block window for baking alerts
   - `ALERT_ATTESTATION_THRESHOLD` - Missed attestation threshold
   - `ALERT_ATTESTATION_BLOCK_WINDOW` - Block window for attestation alerts
   - (Optional) `SEND_ALERT_TO_CLOUDWATCH=true` and `CLOUDWATCH_LOG_GROUP=YourLogGroup` for AWS CloudWatch alerts
   - (Optional) `SEND_ALERT_TO_TELEGRAM=true`, `TELEGRAM_BOT_TOKEN=...`, `TELEGRAM_CHAT_ID=...` for Telegram alerts

3. (Optional) For AWS CloudWatch alerts, install boto3 and configure AWS credentials:
   ```bash
   pip install boto3
   aws configure
   ```

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
- Send alerts if thresholds are exceeded

Database
--------
By default, uses SQLite (`state.db`). You can switch to PostgreSQL by changing the `db_url` in `main.py`.

Customization
-------------
- Adjust thresholds and windows in your `.env` file
- Extend alerting logic in `alerting/alert_manager.py`

---
For more details, see the code and comments in each module.
