import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class RPC:
    def __init__(self, node_url='http://localhost:8732'):
        self.node_url = node_url
        self.current_block = self.get_current_block()
        self.current_level = self.get_current_level()
        # Note: Not used.
        self.level_sliding_window = 100
        # Note: Not used.
        self.max_priority = 15

    def get_url(self, url, timeout=10):
        r = None
        with requests.Session() as s:
            retries = Retry(
                total=5,
                read=5,
                connect=5,
                backoff_factor=0.2,
                status_forcelist=[500, 502, 503, 504])
            s.mount('http://', HTTPAdapter(max_retries=retries))
            s.mount('https://', HTTPAdapter(max_retries=retries))
            print('About to RPC GET '+url)
            r = s.get(url, timeout=timeout)
        return r

    def get_current_block(self, timeout=10):
        url = '{}/monitor/bootstrapped'.format(self.node_url)
        r = self.get_url(url, timeout=timeout)
        return r.json()['block']

    def get_block_info(self, block, timeout=10):
        url = '{}/chains/main/blocks/{}'.format(self.node_url, block)
        r = self.get_url(url, timeout=timeout)
        return r.json()

    def get_latest_finalized_level(self, timeout=10):
        url = '{}/chains/main/blocks/head~2'.format(self.node_url)
        r = self.get_url(url, timeout=timeout)
        header = r.json()['header']
        return header['level'] 

    def get_current_level(self, timeout=10):
        block_info = self.get_block_info(self.current_block, timeout=timeout)
        header = block_info['header']
        return header['level']

    def get_nth_predecessor(self, n, timeout=10):
        block_hash = self.get_current_block(timeout=timeout)
        level = int(self.get_current_level(timeout=timeout))
        url = '{}/chains/main/blocks/{}/header'.format(self.node_url, level - n)
        r = self.get_url(url, timeout=timeout)
        return r.json()

    def get_baking_opportunities_for_level(self, level, timeout=10):
        opportunities = []
        url = '{}/chains/main/blocks/{}~1/helpers/baking_rights'.format(self.node_url, level)
        r = self.get_url(url, timeout=timeout)
        if r:
            opportunities = r.json()
        return opportunities

    def get_baking_opportunities_for_block(self, block_hash, timeout=10):
        opportunities = []
        url = '{}/chains/main/blocks/{}~1/helpers/baking_rights'.format(self.node_url, block_hash)
        r = self.get_url(url, timeout=timeout)
        if r:
            opportunities = r.json()
        return opportunities

    def get_attestation_opportunities_for_level(self, level, timeout=10):
        opportunities = []
        url = '{}/chains/main/blocks/{}~1/helpers/attestation_rights'.format(self.node_url, level)
        r = self.get_url(url, timeout=timeout)
        if r:
            opportunities = r.json()[0]["delegates"]
        return opportunities

    def get_attestation_opportunities_for_block(self, block_hash, timeout=10):
        opportunities = []
        url = '{}/chains/main/blocks/{}~1/helpers/attestation_rights'.format(self.node_url, block_hash)
        r = self.get_url(url, timeout=timeout)
        if r:
            opportunities = r.json()[0]["delegates"]
        return opportunities

    def block_was_attested_by_delegate(self, block_info, delegate_hash):
        was_attesteded = False
        for op in block_info['operations'][0]:
            for item in op['contents']:
                if (item['kind'] == 'attestation' or item['kind'] == 'attestation_with_dal') and item['metadata']['delegate'] == delegate_hash:
                    was_attesteded = True
        return was_attesteded

    def block_iter(self, starting_block):
        block_info = self.get_block_info(starting_block)
        header = block_info['header']
        predecessor = header['predecessor']
        while not predecessor.startswith('BLockGenesis'):
            yield block_info
            block_info = self.get_block_info(predecessor)
            header = block_info['header']
            predecessor = header['predecessor']
        block_info = self.get_block_info(predecessor)
        yield block_info
