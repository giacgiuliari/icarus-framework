#  2020 Tommaso Ciussani and Giacomo Giuliari
"""
Utils for a standardised batched multithreaded computing, in order to best accommodate python's shortcomings.
The class spawns the desired number of processes after dividing the sample list in a desired number of batches.
To reduce biases and thus computation tail times, samples are shuffled before execution.
"""

import math
import pickle
import random
import time
import multiprocessing as mp

from abc import abstractmethod
from typing import Tuple, List, Dict
from icarus_simulator.utils import compute_intervals_uniform


class Multiprocessor:
    def __init__(
        self,
        num_procs: int,
        num_batches: int,
        samples: List,
        process_params: Tuple,
        verbose: bool = False,
    ):
        assert num_procs > 0 and num_batches > 0
        random.seed("DINFK")
        self.num_procs: int = min(mp.cpu_count(), num_procs)
        self.num_batches: int = num_batches
        self.samples: List = samples
        random.shuffle(self.samples)
        self.verbose: bool = verbose
        self.process_params: Tuple = process_params
        samples_len = len(samples)
        per_proc = int(math.ceil((samples_len / num_batches) / self.num_procs))
        self.batch_size: int = per_proc * self.num_procs

    # Override this method only
    @abstractmethod
    def _single_sample_process(
        self, sample, process_result: Dict, params: Tuple
    ) -> None:
        raise NotImplementedError

    def process_batches(self) -> Dict:
        batch_start = 0
        samples_len = len(self.samples)
        idx = 0
        # Run one batch at a time
        result_total = {}
        while batch_start < samples_len:
            print(f"Batch {idx}")
            batch_end = min(batch_start + self.batch_size, samples_len)
            samples_batch = self.samples[batch_start:batch_end]
            batch_start = batch_end
            if self.num_procs == 1:
                dummy_dict = {}
                self._proc_worker(0, dummy_dict, samples_batch)
                dummy_dict[0] = pickle.loads(dummy_dict[0])
                result_batch = self._assemble({}, dummy_dict)
            else:
                result_batch = self._spawn_procs(samples_batch)
            result_total[idx] = result_batch
            idx += 1
        return self._assemble({}, result_total)

    def _spawn_procs(self, samples_batch) -> Dict:
        shared_dict, jobs = mp.Manager().dict(), []
        intervals = compute_intervals_uniform(len(samples_batch), self.num_procs)
        self._verbprint(f"Spawning {len(intervals)} threads")
        for i in range(len(intervals)):
            samples_proc = [s for s in samples_batch[intervals[i][0] : intervals[i][1]]]
            p = mp.Process(
                target=self._proc_worker, args=(i, shared_dict, samples_proc)
            )
            jobs.append(p)
            p.start()
        for proc in jobs:
            proc.join()

        # Unpickle results
        unpickle_dict = {}
        for key in shared_dict:
            unpickle_dict[key] = pickle.loads(shared_dict[key])
        return self._assemble({}, unpickle_dict)

    def _proc_worker(self, proc_id: int, return_dict, samples_proc: List) -> None:
        st = time.time()
        random.seed(f"{proc_id}-{proc_id}-{proc_id}")
        samples_len = len(samples_proc)
        last_min = 0
        thread_result = {}
        for s_id, sample in enumerate(samples_proc):
            minute = int((time.time() - st) / 60)
            if minute != last_min:
                self._verbprint(
                    f"Proc {proc_id}, {(s_id / samples_len) * 100}%, {minute}m"
                )
                last_min = minute
            self._single_sample_process(sample, thread_result, self.process_params)

        return_dict[proc_id] = pickle.dumps(thread_result)
        self._verbprint(
            f"Process {proc_id}, {samples_len} samples, finished in: {time.time() - st}"
        )

    def _verbprint(self, text: str):
        if self.verbose:
            print(text)

    @staticmethod
    def _assemble(final_result: Dict, part_result: Dict) -> Dict:
        for key in part_result:
            final_result.update(part_result[key])
        return final_result
