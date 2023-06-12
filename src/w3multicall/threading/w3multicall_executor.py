from typing import List, Dict, Union, Callable
import logging
import threading
from multiprocessing.pool import ThreadPool
import time
import datetime

from web3 import Web3

from ..multicall import W3Multicall


class W3:

    def __init__(self, w3: Web3, delay_between_call: float):
        self.w3 = w3
        self.delay_between_call = delay_between_call
        self.limit_rate_per_seconds = 1 / self.delay_between_call
        self.last_call_at = 0

    def __repr__(self):
        return '{} {:.2f}/s'.format(self.w3, self.limit_rate_per_seconds)

    def use(self) -> Web3:
        self.last_call_at = time.time()
        return self.w3

    def usable_at(self):
        return self.last_call_at + self.delay_between_call

    def usable_in(self):
        return self.usable_at() - time.time()


class W3Pool:

    def __init__(self, w3s: List[W3], logger: Union[logging.Logger, None] = None):
        self.w3s = w3s
        self.logger = logger

    def add_w3(self, w3: W3) -> 'W3Pool':
        self.w3s.append(w3)
        return self

    def use(self, block: bool = True) -> Union[Web3, None]:
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


class W3MulticallExecutor:

    class Task:
        def __init__(self):
            self.sync = threading.Condition()
            self.creation_time = time.time()
            self.w3_calls: Dict[int, W3Multicall.Call] = {}
            self.w3_results = None
            self.exception: Union[Exception, None] = None

        def __repr__(self):
            return "{}|{}".format(datetime.datetime.fromtimestamp(self.creation_time), len(self.w3_calls))

        def get(self, key):
            with self.sync:
                if self.exception is None and self.w3_results is None:
                    self.sync.wait()
                if self.exception is not None:
                    raise self.exception
                if self.w3_results is None or key not in self.w3_results:
                    raise Exception("Results not available or invalid key")
                return self.w3_results[key]

    class Future:
        def __init__(self, task: 'W3MulticallExecutor.Task', call_key: int):
            self.task = task
            self.call_key = call_key

        def get(self):
            return self.task.get(self.call_key)

    def __init__(self, w3_pool: W3Pool, processes: int, multicall_contract_address = '0xcA11bde05977b3631167028862bE2a173976CA11', batch_max_size: int = 20, tick_duration: float = 0.05, logger: Union[logging.Logger, None] = None):
        self.w3_pool = w3_pool
        self.processes = processes
        self.multicall_contract_address = multicall_contract_address
        self.batch_max_size = batch_max_size
        self.tick_duration = tick_duration
        self.logger = logger
        self.pending_task: Union[W3MulticallExecutor.Task, None] = None
        self.lock = threading.RLock()

        def thread_pool_initializer():
            t = threading.current_thread()
            t.name = 'W3MulticallExecutor-{}'.format(t.name)

        self.thread_pool = ThreadPool(processes=processes, initializer=thread_pool_initializer)
        threading.Thread(target=self.__loop, daemon=True).start()

    def __loop(self):
        while True:
            self.__check_pending_task()
            time.sleep(self.tick_duration)

    def __check_pending_task(self):
        with self.lock:
            if self.pending_task is not None and (time.time() >= self.pending_task.creation_time + self.tick_duration or len(self.pending_task.w3_calls) >= self.batch_max_size):
                if self.logger is not None:
                    self.logger.debug("Triggering task {}".format(self.pending_task))
                task = self.pending_task
                self.pending_task = None
                self.thread_pool.apply_async(func=self.__execute, args=(task, ))

    def __execute(self, task: 'W3MulticallExecutor.Task'):
        if self.logger is not None:
            self.logger.debug("Executing task {}".format(task))
        w3m = W3Multicall(self.w3_pool.use(), self.multicall_contract_address)
        for k in task.w3_calls:
            w3m.add(task.w3_calls[k])
        with task.sync:
            try:
                start = time.time()
                results = w3m.call()
                elapsed = time.time() - start
                if self.logger is not None:
                    self.logger.debug("Multicall executed in {}s".format(elapsed))
                task.w3_results = {}
                for k in task.w3_calls:
                    task.w3_results[k] = results[k]
            except Exception as e:
                task.exception = e
            finally:
                task.sync.notify_all()
        if self.logger is not None:
            self.logger.debug("Task {} completed".format(task))

    def submit(self, call: W3Multicall.Call) -> Future:
        with self.lock:
            if self.pending_task is None:
                self.pending_task = W3MulticallExecutor.Task()
            call_key = len(self.pending_task.w3_calls)
            self.pending_task.w3_calls[call_key] = call
            task = self.pending_task
            self.__check_pending_task()
            return W3MulticallExecutor.Future(task, call_key)

    def cancel_pending(self):
        with self.lock:
            self.pending_task = None
