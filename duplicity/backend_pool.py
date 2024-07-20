# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4; encoding:utf-8 -*-
#
# Copyright 2002 Ben Escoto <ben@emerose.org>
# Copyright 2007 Kenneth Loafman <kenneth@loafman.com>
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import concurrent.futures
import logging
import multiprocessing
import multiprocessing.connection
import os
import sys
import time
import traceback
from collections import Counter
from dataclasses import (
    dataclass,
    field,
)
from datetime import (
    datetime,
    timedelta,
)
from typing import (
    List,
    Optional,
    Dict,
    Iterator,
)

from duplicity import (
    backend,
    config,
    file_naming,
    log,
    path,
    util,
)

if sys.version_info[:2] == (3, 8):
    # patching buggy 3.8 implementation.
    # TODO: remove when 3.8 is deprecated.
    import atexit
    import concurrent.futures.process

    def _python_exit():
        log.Debug("Python 3.8 patched function concurrent.futures.process._python_exit")
        global _global_shutdown
        _global_shutdown = True
        items = list(concurrent.futures.process._threads_wakeups.items())
        for _, thread_wakeup in items:
            if thread_wakeup is not None:
                try:
                    thread_wakeup.wakeup()
                except OSError:
                    pass
        for t, _ in items:
            t.join()

    atexit.unregister(concurrent.futures.process._python_exit)
    concurrent.futures.process._python_exit = _python_exit
    atexit.register(_python_exit)

    def clear(self):
        try:
            while self._reader.poll():
                self._reader.recv_bytes()
        except OSError:
            # OSError may occur if reader already closed and not "clear" is required.
            log.Debug("Python 3.8 patched function concurrent.futures.process._ThreadWakeup.clear")
            pass

    concurrent.futures.process._ThreadWakeup.clear = clear

pool_backend = None


@dataclass
class TrackRecord:
    # result tracking while executed in the pool
    track_id: int
    pid: int
    trace_back: Optional[List[str]] = field(
        default_factory=list
    )  # trace backs can't be pickled, store as string, to get it over into main process
    result: object = None  # must be picklable
    log_prefix: str = ""
    start_time: datetime = field(default=datetime.now())
    stop_time: datetime = field(default=datetime.min)

    def __post_init__(self):
        self.start_time = datetime.now()

    def get_runtime(self) -> timedelta:
        return self.stop_time - self.start_time


def track_cmd(track_id, cmd_name: str, *args, **kwargs):
    """
    wraps the pooled function for time tracking and exception handling.
    Recording the trace back of an exception when still in process pool context
    to point to the right place.
    (This function can't be part of the BackendPool, as then the whole class get pickled)
    """
    global pool_backend
    p = multiprocessing.current_process()
    trk_rcd = TrackRecord(track_id, p.pid, log_prefix=log.PREFIX)  # type: ignore
    # send cmd/process assignment back to pool for tracking.
    try:
        cmd = getattr(pool_backend, cmd_name)
        trk_rcd.result = cmd(*args, **kwargs)
    except Exception as e:
        trk_rcd.result = e
        trk_rcd.trace_back = traceback.format_tb(e.__traceback__)
    trk_rcd.stop_time = datetime.now()
    log.Debug(f"Command done: {trk_rcd} ")
    return trk_rcd


class BackendPool:
    """
    uses concurrent.futures.ProcessPoolExecutor to run backend commands in background
    """

    @dataclass
    class CmdStatus:
        function_name: str
        args: Dict
        kwargs: List
        trk_rcd: Optional[TrackRecord] = None
        done: bool = False

    def __init__(self, url_string, processes=None) -> None:
        config_str = config.dump_dict(config)
        self.ppe = concurrent.futures.ProcessPoolExecutor(
            max_workers=processes,
            initializer=self._process_init,
            initargs=(url_string, config_str),
            mp_context=multiprocessing.get_context(method="spawn"),
        )
        self._command_queue = []
        self._track_id = 0
        self.all_results: List[TrackRecord] = []
        self._all_futures: List[concurrent.futures.Future] = []
        self.peak_in_queue = 0
        self._command_throttle_stats = []
        self._last_results_reported = 0

    def __enter__(self):
        return self.ppe

    def __exit__(self, type, value, traceback):
        self.shutdown()

    @staticmethod
    def _process_init(url_string, config_dump):
        global pool_backend
        config.load_dict(config_dump, config)
        pid = os.getpid()
        pool_nr = multiprocessing.current_process()._identity[0]
        # get the multiprocessing logger with stderr stream handler added
        log.setup()
        log.PREFIX = f"Pool{pool_nr}: "
        log.setverbosity(config.verbosity)
        logger = multiprocessing.log_to_stderr(level=logging.getLevelName(log.LevelName(config.verbosity)))
        log.Info(f"Staring pool process with pid: {pid}")
        file_naming.prepare_regex()
        util.start_debugger()
        backend.import_backends()
        pool_backend = backend.get_backend(url_string)

    def command(self, func_name, args=(), kwds=None):
        """
        run function in a pool of independent processes. Call function by name.
        func_name: name of the backend method to execute
        args: positional arguments for the method
        kwds: key/value  arguments for the method

        Returns a unique ID for each command, increasing int
        """
        if kwds is None:
            kwds = {}
        self._track_id += 1
        self._command_queue.append(
            self.ppe.submit(
                track_cmd,
                self._track_id,
                func_name,
                *args,
            ),
        )
        self._collect_finished_cmds()
        return self._track_id

    def _raise_exception_if_any(self, track_rcrd):
        """
        raise the exception stored in `track_rcrd` if it occurred while running the command
        """
        if isinstance(track_rcrd.result, Exception):
            exception_str = f"{''.join(track_rcrd.trace_back)}\n{track_rcrd.result}"
            log.Debug(f"Exception thrown in pool: \n{exception_str}")
            if hasattr(track_rcrd.result, "code"):
                log.FatalError(
                    f"Exception {track_rcrd.result.__class__.__name__} in background "
                    f"pool {track_rcrd.log_prefix}. "
                    "For trace back set loglevel to DEBUG and check output for given pool.",
                    code=track_rcrd.result.code,  # type: ignore
                )
            else:
                raise track_rcrd.result

    def _collect_finished_cmds(self):
        """
        store finished results in `all_results` and remove command from queue
        """
        try:
            finished_commands = concurrent.futures.as_completed(self._command_queue, timeout=0.1)
            for result in finished_commands:
                track_rcrd = result.result(timeout=0)
                self._raise_exception_if_any(track_rcrd)
                self.all_results.append(track_rcrd)
                self._all_futures.append(result)
                self._command_queue.remove(result)
                self.peak_in_queue = max(self.peak_in_queue, len(self._command_queue))
        except concurrent.futures._base.TimeoutError:
            pass

    def command_throttled(self, func_name, commands_in_buffer=1, args=(), kwds=None):
        """
        block, if queue gets bigger then number of workers + commands_in_buffer.
        Means this function my block a while to process queue and returns if enough
        queue items has been processed.
        func_name: name of the backend method to execute
        commands_in_buffer = number of commands that are queue for execution
        args: positional arguments for the method
        kwds: key/value  arguments for the method

        Returns a unique ID for each command, increasing int
        """

        if kwds is None:
            kwds = {}

        # define accepted queue buffer.
        max_pending_queue_len = self.ppe._max_workers + commands_in_buffer  # type: ignore

        start = datetime.now()
        if len(self._command_queue) >= max_pending_queue_len:
            # queue full wait for free slot
            finished_commands = concurrent.futures.as_completed(self._command_queue)
            next(finished_commands)  # blocking until next finished

        self._command_throttle_stats.append((datetime.now() - start).total_seconds())
        log.Debug(f"Command delayed by {self._command_throttle_stats[-1]:.2f}")
        # queue command
        track_id = self.command(func_name, args, kwds)

        return track_id

    def get_queue_length(self) -> int:
        return len(self._command_queue)

    def results_since_last_call(self, from_pos=None) -> Iterator[TrackRecord]:
        """
        collect results from commands finished since last run of this method.
        This method should be called from one receiver only, as it keep track of what was send internally.
        param:
            from_pos: use to overwrite the internal pointer `__last_results_reported`

        return:
            list of future results
        """
        self._collect_finished_cmds()
        if from_pos is not None:
            self._last_results_reported = from_pos
        end = len(self.all_results)
        for result in self.all_results[self._last_results_reported : end]:
            yield result
            self._last_results_reported = end

    def get_stats(self, last_index=None):
        vals = [x.get_runtime().total_seconds() for x in self.all_results[:last_index]]
        count = len(vals)
        if count > 0:
            avg_time = sum(vals) / count
            max_time = max(vals)
            min_time = min(vals)
            if len(self._command_throttle_stats) > 0:
                avg_throttle = sum(self._command_throttle_stats) / len(self._command_throttle_stats)
                max_throttle = max(self._command_throttle_stats)
                min_throttle = min(self._command_throttle_stats)
            else:
                avg_throttle = max_throttle = min_throttle = -1
        else:
            avg_time = max_time = min_time = avg_throttle = max_throttle = min_throttle = -1
        pool_usage = Counter([x.log_prefix for x in self.all_results[:last_index]])

        log.Debug(
            f"count: {count}, avg: {avg_time}, max: {max_time}, min: {min_time}, pool usage: {pool_usage}, "
            f"peak in queue: {self.peak_in_queue}, avg throttle: {avg_throttle}"
        )
        return {
            "count": count,
            "time": {"avg": avg_time, "max": max_time, "min": min_time},
            "throttle": {"avg": avg_throttle, "max": max_throttle, "min": min_throttle},
            "pool_usage": pool_usage,
            "peak_in_queue": self.peak_in_queue,
        }

    def shutdown(self, *args):
        concurrent.futures.wait(self._all_futures, timeout=0.5)  # workaround to make py3.8 more stable
        log.Debug("Process Pool: Start shutdown.")
        self.ppe.shutdown(*args)
        log.Debug("Process Pool: Shutdown done.")


# code to run/test the pool independent, not relevant for duplicity
if __name__ == "__main__":
    from duplicity import config, log

    log.setup()
    log.add_file("/tmp/tmp.log")
    config.verbosity = log.INFO
    log.setverbosity(config.verbosity)
    backend.import_backends()
    config.async_concurrency = 4
    config.num_retries = 2
    url = "file:///tmp/test_direct"
    bw = backend.get_backend(url)
    # ^^^^^^^^^^ above commands are only there for mocking a duplicity config

    start_time = time.time()
    bpw = BackendPool(url, processes=config.async_concurrency)
    results: List[TrackRecord] = []
    with bpw as pool:
        # issue tasks into the process pool
        import pathlib

        if len(sys.argv) > 1:
            src = sys.argv[1]
        else:
            src = "./"
        for file in [file for file in pathlib.Path(src).iterdir() if file.is_file()]:
            source_path = path.Path(file.as_posix())
            bpw.command(bw.put_validated.__name__, args=(source_path, source_path.get_filename()))  # type: ignore
            cmd_results = [x for x in bpw.results_since_last_call()]
            log.Info(f"got: {len(cmd_results)}, cmd left: {bpw.get_queue_length()}, track_id: {bpw._track_id}")
            results.extend(cmd_results)

        # wait for tasks to complete
        suppress_log = False
        while True:
            cmd_results = [x for x in bpw.results_since_last_call()]
            if len(cmd_results) > 0 or not suppress_log:
                log.Info(
                    f"got: {len(cmd_results)}, {not suppress_log}, "
                    f"precessed {len(results)} cmd left: {bpw.get_queue_length()}, track_id: {bpw._track_id}"
                )
                suppress_log = False
            if len(cmd_results) == 0:
                suppress_log = True

            results.extend(cmd_results)
            if bpw.get_queue_length() == 0:
                break

        bpw.get_stats(last_index=-1)
        input("Press Enter to continue...")
    # process pool is closed automatically

    log.Notice(f"Bytes written: {sum([int(x.result) for x in results])}")  # type: ignore
    log.Notice(f"Time elapsed: {time.time() - start_time}")
