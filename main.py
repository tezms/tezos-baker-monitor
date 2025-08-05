# First load the environment variables from .env file, since they are needed for some of the rest of the imports
from dotenv import load_dotenv
load_dotenv()
import os
import time
from rpc.rpc_client import RPC
from alerting.alert_manager import send_alert
from database.db import get_engine, get_session, init_db, State, BlockBaking, BlockAttestation

# Load environment variables from .env

RPC_URL = os.getenv('RPC_URL')
DELEGATES_TO_MONITOR_PARAMETER = os.getenv('DELEGATES_TO_MONITOR_PARAMETER')
BLOCK_SLIDING_WINDOW_SIZE = os.getenv('BLOCK_SLIDING_WINDOW_SIZE') 
ALERT_BAKING_THRESHOLD = int(os.getenv('ALERT_BAKING_THRESHOLD'))
ALERT_BAKING_BLOCK_WINDOW = int(os.getenv('ALERT_BAKING_BLOCK_WINDOW'))
ALERT_ATTESTATION_THRESHOLD = int(os.getenv('ALERT_ATTESTATION_THRESHOLD'))
ALERT_ATTESTATION_BLOCK_WINDOW = int(os.getenv('ALERT_ATTESTATION_BLOCK_WINDOW'))
ALERT_INACTIVE_STATE_THRESHOLD = int(os.getenv('ALERT_INACTIVE_STATE_THRESHOLD', 600))  # Default to 10 minutes
delegates = [addr.strip() for addr in DELEGATES_TO_MONITOR_PARAMETER.split(',')]

# Main function to monitor delegates

def get_last_processed_level(session):
    state = session.query(State).first()
    return state.last_processed_level if state else 0

def save_last_processed_level(session, level):
    now = int(time.time())
    state = session.query(State).first()
    if state:
        state.last_processed_level = level
        state.timestamp = now
    else:
        state = State(last_processed_level=level, timestamp=now)
        session.add(state)
    session.commit()

def process_baking_rights(session, rpc, block_level, delegates):
    baking_opportunities = rpc.get_baking_opportunities_for_level(block_level)
    baking_round0_right = baking_opportunities[0]['delegate']
    print(f"Baking rights round 0: {baking_round0_right}")
    if baking_round0_right in delegates:
        print(f"Delegate {baking_round0_right} has baking rights for block {block_level}")
        block_info = rpc.get_block_info(block_level)
        baker = block_info['metadata']['baker']
        if baker != baking_round0_right:
            print(f"Delegate {baking_round0_right} has baking rights for block {block_level}, but it was baked by {baker}.")
            block_entry = BlockBaking(block_level=block_level, delegate=baking_round0_right, successful=0)
        else:
            print(f"Delegate {baking_round0_right} successfully baked block {block_level}")
            block_entry = BlockBaking(block_level=block_level, delegate=baking_round0_right, successful=1)
        session.add(block_entry)
        session.commit()

def process_attestation_rights(session, rpc, block_level, delegates):
    attestation_opportunities = rpc.get_attestation_opportunities_for_level(block_level)

    for attestation_opportunity in attestation_opportunities:
        attestation_delegate = attestation_opportunity['delegate']
        if attestation_delegate in delegates:
            print(f"Delegate {attestation_delegate} has attestation rights for block {block_level}")
            block_info = rpc.get_block_info(block_level)
            operations = block_info['operations']
            attested = False
            for attestation in operations[0]:
                for content in attestation['contents']:
                    if (content['kind'] == 'attestation_with_dal' or content['kind'] == 'attestation') and content['metadata']['delegate'] == attestation_delegate:
                        print(f"Delegate {attestation_delegate} successfully attested block {block_level}")
                        attested = True
                        break
                    if content['kind'] == 'attestations_aggregate':
                        for committee in content['metadata']['committee']:
                            if committee['delegate'] == attestation_delegate:
                                print(f"Delegate {attestation_delegate} successfully attested block {block_level}")
                                attested = True
                                break
            if attested:
                block_entry = BlockAttestation(block_level=block_level, delegate=attestation_delegate, successful=1)
            else:
                print(f"Delegate {attestation_delegate} did NOT attest block {block_level}")
                block_entry = BlockAttestation(block_level=block_level, delegate=attestation_delegate, successful=0)
            session.add(block_entry)
            session.commit()

def remove_entries_from_block_baking(session, current_block_level, window_blocks):
    """
    Remove entries from block_baking older than current_block_level - window_blocks.
    """
    cutoff_level = current_block_level - window_blocks
    deleted = session.query(BlockBaking).filter(BlockBaking.block_level < cutoff_level).delete()
    session.commit()
    print(f"Removed {deleted} entries from block_baking older than block level {cutoff_level}.")

def remove_entries_from_block_attestations(session, current_block_level, window_blocks):
    """
    Remove entries from block_attestation older than current_block_level - window_blocks.
    """
    cutoff_level = current_block_level - window_blocks
    deleted = session.query(BlockAttestation).filter(BlockAttestation.block_level < cutoff_level).delete()
    session.commit()
    print(f"Removed {deleted} entries from block_attestation older than block level {cutoff_level}.")

def check_last_processed_timestamp(session, max_age_seconds):
    """
    Checks if the last processed timestamp in State is older than max_age_seconds.
    Sends an alert if the state is stale.
    """
    state = session.query(State).first()
    if state and state.timestamp:
        now = int(time.time())
        age = now - state.timestamp
        if age > max_age_seconds:
            send_alert(f"!!! State is stale! Last processed timestamp is {age} seconds old.")
    else:
        print("No timestamp found in state table.")

def check_for_baking_alerts(session, delegates, threshold):
    """
    Checks if missed bakings in block_baking table meet or exceed threshold.
    Sends alert if so.
    """
    for delegate in delegates:
        missed_count = session.query(BlockBaking).filter_by(delegate=delegate, successful=0).count()
        if missed_count >= threshold:
            send_alert(f"!!! Delegate {delegate} missed {missed_count} bakings (threshold: {threshold})!")

def check_for_attestation_alerts(session, delegates, threshold):
    """
    Checks if missed attestations in block_attestation table meet or exceed threshold.
    Sends alert if so.
    """
    for delegate in delegates:
        missed_count = session.query(BlockAttestation).filter_by(delegate=delegate, successful=0).count()
        if missed_count >= threshold:
            send_alert(f"!!! Delegate {delegate} missed {missed_count} attestations (threshold: {threshold})!")

def main():
    # Database setup
    db_url = 'sqlite:///state.db'  # Change to PostgreSQL if needed
    engine = get_engine(db_url)
    init_db(engine)
    session = get_session(engine)

    # Initialize RPC client
    rpc = RPC(node_url=RPC_URL)

    # Get last processed level from DB
    last_processed_level = get_last_processed_level(session)
    print(f"Last processed level: {last_processed_level}")

    # Check for staled state
    check_last_processed_timestamp(session, ALERT_INACTIVE_STATE_THRESHOLD)

    # Get latest finalized level
    latest_finalized_level = rpc.get_latest_finalized_level()
    print(f"Latest finalized Tezos level: {latest_finalized_level}")

    remove_entries_from_block_baking(session, latest_finalized_level, ALERT_BAKING_BLOCK_WINDOW)
    remove_entries_from_block_attestations(session, latest_finalized_level, ALERT_ATTESTATION_BLOCK_WINDOW)

    start_block = latest_finalized_level - int(BLOCK_SLIDING_WINDOW_SIZE) + 1
    if start_block < last_processed_level:
        start_block = last_processed_level + 1
        print("Start block set to last_processed_level:", last_processed_level)

    for block_level in range(start_block, latest_finalized_level + 1):
        print("Processing block:", block_level)
        process_baking_rights(session, rpc, block_level, delegates)
        process_attestation_rights(session, rpc, block_level, delegates)
        
    check_for_baking_alerts(session, delegates, ALERT_BAKING_THRESHOLD)
    check_for_attestation_alerts(session, delegates, ALERT_ATTESTATION_THRESHOLD)
    save_last_processed_level(session, latest_finalized_level)
    print("All blocks processed. Last processed level saved to database.")

if __name__ == "__main__":
    main()
