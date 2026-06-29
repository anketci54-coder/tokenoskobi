
import time, resource, collections

class FixedRing:
    def __init__(self, maxlen=256):
        self.buf=collections.deque(maxlen=maxlen)
    def add(self, v):
        self.buf.append(v)
    def count(self):
        return len(self.buf)
    def maxlen(self):
        return self.buf.maxlen

class RuntimeObservability:
    def __init__(self, maxlen=256):
        self.latency_ns=FixedRing(maxlen)
        self.queue_depth=FixedRing(maxlen)
        self.exception_count=0
        self.fail_closed_count=0
        self.dropped_event_count=0
        self.logger_backlog=FixedRing(maxlen)
        self.raw_payload_seen=False
    def start_ns(self):
        return time.perf_counter_ns()
    def end_ns(self, start_ns, queue_depth=0, logger_backlog=0):
        delta=time.perf_counter_ns()-start_ns
        if delta < 0:
            self.fail_closed_count += 1
            delta=0
        self.latency_ns.add(delta)
        self.queue_depth.add(int(queue_depth))
        self.logger_backlog.add(int(logger_backlog))
        return delta
    def record_exception(self):
        self.exception_count += 1
    def record_fail_closed(self):
        self.fail_closed_count += 1
    def record_drop(self):
        self.dropped_event_count += 1
    def rss_kb(self):
        return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    def snapshot(self):
        return {
            "latency_count": self.latency_ns.count(),
            "latency_buffer_maxlen": self.latency_ns.maxlen(),
            "queue_depth_count": self.queue_depth.count(),
            "logger_backlog_count": self.logger_backlog.count(),
            "exception_count": self.exception_count,
            "fail_closed_count": self.fail_closed_count,
            "dropped_event_count": self.dropped_event_count,
            "rss_kb": self.rss_kb(),
            "raw_payload_seen": self.raw_payload_seen
        }
