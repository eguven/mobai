import heapq


class PriorityQueue(object):
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


def heuristic(a, b):
    ax, ay = a
    bx, by = b
    return abs(ax - bx) + abs(ay - by)


def a_star_search(map, start, end):
    '''A* search. Should be bound to map'''
    assert isinstance(start, tuple) and isinstance(end, tuple)
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    # initialize with start
    came_from[start] = None
    cost_so_far[start] = 0

    while not frontier.empty():
        current = frontier.get()
        if current == end:
            break

        for neighbor in map.get_tile(*current).neighbor_positions():
            new_cost = cost_so_far[current] + 1  # move costs 1
            if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                # no entry yet or we found shorter path
                cost_so_far[neighbor] = new_cost
                priority = new_cost + heuristic(end, neighbor)
                frontier.put(neighbor, priority)
                came_from[neighbor] = current

    assert current == end
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    return reversed(path)
