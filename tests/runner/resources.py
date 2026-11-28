import asyncio


class ResourceBlocked(RuntimeError):
    pass


class Resources:
    def __init__(self):
        self.locks = {}
        self.blocked = {}

    async def acquire(self, names):
        acquired = []
        try:
            for name in sorted(set(names)):
                lock = self.locks.setdefault(name, asyncio.Lock())
                await lock.acquire()
                acquired.append(lock)
                if name in self.blocked:
                    raise ResourceBlocked(self.blocked[name])
            return acquired
        except BaseException:
            self.release(acquired)
            raise

    @staticmethod
    def release(locks):
        for lock in reversed(locks):
            lock.release()

    def poison(self, names, reason):
        # The mutex can wake waiters, but no waiter may use the still-owned device.
        for name in names:
            self.blocked[name] = reason
