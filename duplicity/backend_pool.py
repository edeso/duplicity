from dataclasses import dataclass, field
import multiprocessing
import os
import sys
import time
from collections import deque
from datetime import datetime, timedelta
import concurrent.futures
import traceback
from typing import List, Optional, Dict, Tuple

from duplicity import (
    backend,
    log,
    path,
)

multiprocessing.set_start_method("fork")
cmd_tracker = multiprocessing.Queue()


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
    start_time = datetime.now()
    stop_time = datetime.min

    def get_runtime(self) -> timedelta:
        if self.stop_time == datetime.min:
            return datetime.now() - self.start_time
        else:
            return self.stop_time - self.start_time


def track_cmd(track_id, cmd_name: str, *args, **kwargs):
    """
    wraps the pooled function for time tracking and exception handling.
    Recording the trace back of an exception when still in process pool context
    to point to the right place.
    (This function can't be part of the BackendPool, as then the whole class get pickled)
    """
    global pool_backend, cmd_tracker
    p = multiprocessing.current_process()
    trk_rcd = TrackRecord(track_id, p.pid, log_prefix=log.PREFIX)  # type: ignore
    # send cmd/process assignment back to pool for tracking.
    cmd_tracker.put(trk_rcd, timeout=5)
    try:
        cmd = getattr(pool_backend, cmd_name)
        trk_rcd.result = cmd(*args, **kwargs)
    except Exception as e:
        trk_rcd.result = e
        trk_rcd.trace_back = traceback.format_tb(e.__traceback__)
    trk_rcd.stop_time = datetime.now()
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
        self.ppe = concurrent.futures.ProcessPoolExecutor(
            max_workers=processes, initializer=self._process_init, initargs=(url_string,)
        )
        self._command_queue = deque()
        self._track_id = 0
        self.all_results: List[TrackRecord] = []
        self.cmd_status: Dict[int, BackendPool.CmdStatus] = {}

    def __enter__(self):
        return self.ppe

    def __exit__(self, type, value, traceback):
        self.shutdown()

    def _process_init(self, url_string):
        pid = os.getpid()
        pool_nr = multiprocessing.current_process()._identity[0]
        log.PREFIX = f"Pool{pool_nr}: "
        log.Info(f"Staring pool process with pid: {pid}")
        global pool_backend
        pool_backend = backend.get_backend(url_string)

    def command(self, func_name, args=(), kwds={}):
        """
        run function in a pool of independent processes. Call function by name.
        func_name: name of the backend method to execute
        args: positional arguments for the method
        kwds: key/value  arguments for the method

        Returns a unique ID for each command, increasing int
        """
        self._track_id += 1
        self._command_queue.append(
            (
                self._track_id,
                self.ppe.submit(
                    track_cmd,
                    self._track_id,
                    func_name,
                    *args,
                ),
            )
        )
        self.cmd_status[self._track_id] = self.CmdStatus(function_name=func_name, args=args, kwargs=kwds)
        return self._track_id

    def collect_results(self) -> Tuple[int, Dict]:
        """
        collect results from commands finished since last run of this method
        return:
            number of commands in the queue,
            dictionary of [track_id, result]
        """
        results: Dict[int, TrackRecord] = {}
        for _ in range(len(self._command_queue)):  # iterate though deque
            try:
                # exceptions should be catch in track_cmd(), otherwise it get raised here
                self._command_queue[0][1].exception(timeout=0)

                if self._command_queue[0][1].done():
                    id, async_result = self._command_queue.popleft()
                    track_rcrd = async_result.result(timeout=0)
                    if isinstance(track_rcrd.result, (Exception)):
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
                    results[track_rcrd.track_id] = track_rcrd
                else:
                    # shift to next command result
                    self._command_queue.rotate(-1)
            except (concurrent.futures.TimeoutError, concurrent.futures.CancelledError):
                self._command_queue.rotate(-1)
        self.all_results.extend(results.values())
        for id, tr in results.items():
            self.cmd_status[id].trk_rcd = tr
            self.cmd_status[id].done = True

        return (len(self._command_queue), results)

    def get_stats(self, last_index=None):
        vals = [x.get_runtime().total_seconds() for x in self.all_results[:last_index]]
        count = len(vals)
        if count > 0:
            avg_time = sum(vals) / count
            max_time = max(vals)
            min_time = min(vals)
        else:
            avg_time = max_time = min_time = -1
        log.Debug(f"count: {count}, avg: {avg_time}, max: {max_time}, min: {min_time}")
        return {"count": count, "avg": avg_time, "max": max_time, "min": min_time}

    def shutdown(self, *args):
        self.ppe.shutdown(*args)


# code to run/test the pool independent, not relevant for duplicity
if __name__ == "__main__":
    from duplicity import config, log

    log.setup()
    log.add_file("/tmp/tmp.log")
    log.setverbosity(log.DEBUG)
    backend.import_backends()
    config.async_concurrency = multiprocessing.cpu_count()
    config.num_retries = 2
    url = "file:///tmp/back4"
    bw = backend.get_backend(url)
    # ^^^^^^^^^^ above commands are only there for moking a duplicity config

    start_time = time.time()
    bpw = BackendPool(url, processes=config.async_concurrency)
    results = {}
    with bpw as pool:
        # issue tasks into the process pool
        import pathlib

        if len(sys.argv) > 1:
            src = sys.argv[1]
        else:
            src = "./"
        for file in [file for file in pathlib.Path(src).iterdir() if file.is_file()]:
            source_path = path.Path(file.as_posix())
            bpw.command(bw.put_validated, args=(source_path, source_path.get_filename()))  # type: ignore
            commands_left, cmd_results = bpw.collect_results()
            log.Info(f"got: {len(cmd_results)}, cmd left: {commands_left}, track_id: {bpw._track_id}")
            results.update(cmd_results)

        # wait for tasks to complete
        while True:
            commands_left, cmd_results = bpw.collect_results()
            log.Info(
                f"got: {len(cmd_results)}, "
                "precessed {len(results)} cmd left: {commands_left}, track_id: {bpw._track_id}"
            )
            results.update(cmd_results)
            if commands_left == 0:
                break

        bpw.get_stats(last_index=-1)
    # process pool is closed automatically

    log.Notice(f"Bytes written: {sum([x.result for x in results.values()])}")
    log.Notice(f"Time elapsed: {time.time() - start_time}")
