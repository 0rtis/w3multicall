from typing import List, Dict, Union, Callable
import time
import logging
from web3 import Web3


class W3:

    def __init__(self, _web3: Web3, delay_between_call: float, label: Union[str, None] = None):
        self.web3 = _web3
        self.delay_between_call = delay_between_call
        self.limit_rate_per_seconds = 1 / self.delay_between_call
        self.last_call_at = 0
        self.label = hex(id(self)) if label is None else label

    def __repr__(self):
        return '{} {:.2f}/s'.format(self.label, self.limit_rate_per_seconds)

    def use(self) -> Web3:
        self.last_call_at = time.time()
        return self.web3

    def usable_at(self):
        return self.last_call_at + self.delay_between_call

    def usable_in(self):
        return self.usable_at() - time.time()


class W3Pool:
    """
    Pool of W3 instances
    """

    def __init__(self, w3s: List[W3], logger: Union[logging.Logger, None] = None):
        """
        :param w3s: list of W3 instances
        :param logger: (optional) logging.Logger
        """
        self.w3s = w3s
        self.logger = logger

    def add_w3(self, w3: W3) -> 'W3Pool':
        self.w3s.append(w3)
        return self

    def use(self, block: bool = True) -> Union[Web3, None]:
        """
        Return a Web3 instance that will not hit the rate limit upon calling (may block until the rate limit windows has passed)
        :param block: (default: true) block until a Web3 instance is available
        :return: Web3 instance
        """
        next_available: Union[W3, None] = None

        for i in range(len(self.w3s)):
            tau = self.w3s[i].usable_in()
            if tau <= 0:
                if self.logger is not None:
                    self.logger.debug("Using {}".format(self.w3s[i]))
                return self.w3s[i].use()
            if next_available is None or tau < next_available.usable_in():
                next_available = self.w3s[i]

        if next_available is None:
            raise Exception("No Web3 instance found")

        if block:
            sleep = next_available.usable_in()
            if sleep > 0:
                if self.logger is not None:
                    self.logger.warning("Waiting {}s for {}".format(sleep, next_available))
                time.sleep(sleep)
            self.logger.debug("Using {}".format(next_available))
            return next_available.use()
        else:
            return None

