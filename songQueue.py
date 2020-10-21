import asyncio
import itertools
import random


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]
    
    def size(self):
        return self.__len__()


async def main():
    songs = SongQueue()
    await songs.put(123)
    await songs.put(2)
    print(type(songs))
    print(songs.size())

if __name__ == "__main__":
    asyncio.run(main())