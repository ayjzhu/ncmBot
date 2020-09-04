class QueueList():
    def __init__(self):
        self.items = []

    def isEmpty(self):
        return self.items == []
    
    def enqueue(self, item):
        self.items.insert(0, item)
    
    def dequeue(self):
        return self.items.pop()
    
    def size(self):
        return len(self.items)
    
    def front(self):
        return self.items[-1]
    
    def back(self):
        return self.items[0]
    
    def clear(self):
        self.items.clear()