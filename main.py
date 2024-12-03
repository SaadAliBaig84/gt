from flownetwork import FlowNetwork

from tkinter import *
from tkinter.filedialog import askopenfilename as ofdialog
from math import sqrt, sin, cos, pi, degrees
from time import sleep

class GraphVertex:
    RADIUS = 30

    def __init__(self, name, point, fake=False):
        self.name = name
        self.point = point
        self.fake = fake

class GraphEdge:
    ARROW_SIZE = 20

    def __init__(self, vertex1, vertex2, capacity=None, flow=None):
        self.source = vertex1
        self.sink = vertex2
        self.capacity = capacity
        self.flow = flow
        self.fake = False

        self.red = False

        radius = GraphVertex.RADIUS

        (x1, y1) = vertex1.point
        (x2, y2) = vertex2.point
        a = x2 - x1
        b = y2 - y1
        c = sqrt(a ** 2 + b ** 2)

        if c == 0:
            raise ValueError("points cannot be equal")

        cosA = a / c
        sinA = b / c
        dx = radius * cosA
        dy = radius * sinA

        self.point1 = (x1 + dx, y1 + dy)
        if vertex1.fake:
            self.point1 = (x1, y1)
        self.point2 = (x2 - dx, y2 - dy)
        if vertex2.fake:
            self.point2 = (x2, y2)
            self.fake = True
        self.textPoint = ((x1 * 2 + x2) // 3, (y1 * 2 + y2) // 3)

    def setRed(self, red=True):
        self.red = red

class GraphGenerator:

    @staticmethod
    def levels(flownetwork, source, sink):
        L = {}
        for vertex in flownetwork.adj:
            path = flownetwork.maxLength_path(vertex, sink)
            L[vertex] = (len(path), path)
        return L

    @staticmethod
    def fromFlowNetwork(flownetwork, source, sink, viewSize, path=[]):
        (width, height) = viewSize
        vertices = []
        vertexByNames = {}
        edges = []

        LEFT_MARGIN = 180
        VMARGIN = 140
        MIDDLE = (LEFT_MARGIN, height // 2)

        def coordGenerator(level):
            x = (level + 1) * LEFT_MARGIN
            y = MIDDLE[1]
            margin = 0
            yield (x, y)
            while True:
                margin += VMARGIN
                yield (x, y - margin)
                yield (x, y + margin)

        L = GraphGenerator.levels(flownetwork, source, sink)
        levels = {}

        for v in L:
            level = L[v][0]
            if level in levels:
                levels[level].append(v)
            else:
                levels[level] = [v]

        maxLevel = max(levels.keys())

        levelNames = list(levels.keys())
        levelNames.sort(reverse=True)

        queue = []
        for level in levelNames:
            queue.append(levels[level])

        pointCoords = {}
        for index, level in zip(range(len(queue)), queue):
            if not index in pointCoords:
                pointCoords[index] = coordGenerator(index)

            for vertex in level:
                currentVertex = GraphVertex(vertex, next(pointCoords[index]))
                vertices.append(currentVertex)
                vertexByNames[vertex] = currentVertex

        for vertex in vertices:
            for edge in flownetwork.get_edges(vertex.name):
                if edge.reverse:
                    continue

                beginLevel = maxLevel - L[edge.source][0]
                endLevel = maxLevel - L[edge.sink][0]

                fakePath = []
                if abs(beginLevel - endLevel) > 1:
                    if beginLevel > endLevel:
                        beginLevel, endLevel = endLevel, beginLevel
                    for i in range(beginLevel + 1, endLevel):
                        if not i in pointCoords:
                            pointCoords[i] = coordGenerator(i)

                        fakeVertex = GraphVertex("", next(pointCoords[i]), True)
                        fakePath.append(fakeVertex)

                if len(fakePath) == 0:
                    newEdge = GraphEdge(vertexByNames[edge.source], vertexByNames[edge.sink], edge.capacity, flownetwork.flow[edge])
                    if edge in path or edge.redge in path:
                        newEdge.setRed()
                    edges.append(newEdge)
                else:
                    newEdge = GraphEdge(vertexByNames[edge.source], fakePath[0])
                    newEdges = [newEdge]

                    for fakeIndex in range(len(fakePath) - 1):
                        newEdge = GraphEdge(fakePath[fakeIndex], fakePath[fakeIndex + 1])
                        newEdges.append(newEdge)

                    lastEdge = GraphEdge(fakePath[-1], vertexByNames[edge.sink])
                    newEdges.append(lastEdge)

                    newEdges[len(newEdges) // 2].capacity = edge.capacity
                    newEdges[len(newEdges) // 2].flow = flownetwork.flow[edge]

                    if edge in path or edge.redge in path:
                        for e in newEdges:
                            e.setRed()
                    edges += newEdges

        return (vertices, edges)

class GraphCanvas(Canvas):

    def __init__(self, parent, flownetwork=None):
        super().__init__(parent, width=1500, height=800)
        self.vertices = []
        self.edges = []
        if flownetwork is not None:
            self.setFlowNetwork(flownetwork)
        self.draw()

    def setFlowNetwork(self, flownetwork, path=[]):
        (self.vertices, self.edges) = GraphGenerator.fromFlowNetwork(flownetwork, 's', 't', (1920, 1080), path)
        self.draw()


    def draw(self):
        self.delete("all")
        for vertex in self.vertices:
            self._draw_vertex(vertex)
        for edge in self.edges:
            self._draw_edge(edge)
        # for edge in self.min_cut_edges:
        #     self._draw_min_cut_edge(edge)

    def _draw_vertex(self, vertex):
        radius = GraphVertex.RADIUS
        (x, y) = vertex.point
        self.create_oval((x - radius, y - radius, x + radius, y + radius))
        self.create_text(vertex.point, text=vertex.name,font=("Helvetica", 20, "bold"))

    def _draw_edge(self, edge):
        VPADDING = 14
        PADDING = 34

        # Fix: Changed color to a valid name "black" instead of "systemTextColor"
        color = "red" if edge.red else "black"

        if edge.fake:
            self.create_line(edge.point1 + edge.point2, fill=color)
        else:
            self.create_line(edge.point1 + edge.point2, fill=color, arrow=LAST)
        if not edge.capacity is None:
            (x, y) = edge.textPoint
            self.create_rectangle((x - PADDING, y - VPADDING, x + PADDING, y + VPADDING), fill=self['background'])
            text = "{}/{}".format(edge.flow, edge.capacity)
            self.create_text(edge.textPoint, text=text, font=("Helvetica", 20, "bold"))


if __name__ == "__main__":
    root = Tk()
    root.title("Ford-Fulkerson algorithm")
    canvas = GraphCanvas(root)
    canvas.pack()

    gen = iter([])

    def onOpenBtnClicked():
        filename = ofdialog()
        try:
            with open(filename) as f:
                vertices = []
                edges = []

                for line in f:
                    source, sink, capacity = line.split(' ')
                    if not source in vertices:
                        vertices.append(source)
                    if not sink in vertices:
                        vertices.append(sink)
                    edges.append((source, sink, int(capacity)))

                g = FlowNetwork()
                for v in vertices:
                    g.add_vertex(v)
                for f, t, c in edges:
                    g.add_edge(f, t, c)

                canvas.setFlowNetwork(g)
                global gen
                gen = g.max_flow_gen('s', 't')
        except FileNotFoundError:
            pass
        else:
            stepBtn['state'] = NORMAL
            answerLbl['text'] = ""


   

    openBtn = Button(root, text="Open", command=onOpenBtnClicked,
                    width=20, height=2, font=("Helvetica", 12, "bold"),
                    bg="#4CAF50", fg="white", relief="solid")
    openBtn.pack(padx=10, pady=10)

 
    def onStepBtnClicked():
        ans = None
        try:
            value = next(gen)
            if type(value) is int:
                ans = value
                raise StopIteration()

            nw, p = value
            canvas.setFlowNetwork(nw, p)

          
        except StopIteration:
            stepBtn['state'] = DISABLED
            answerLbl['text'] = "Answer: " + str(ans) + ",  Min Cut: " 
            answerLbl.config(font=("Helvetica", 30, "bold"))

    stepBtn = Button(root, text="Step", command=onStepBtnClicked, width=20, height=2, font=("Helvetica", 12),bg="#4CAF50", fg="white", relief="solid")
    stepBtn.pack(padx=10, pady=10)
    answerLbl = Label(root)
    answerLbl.pack()
    root.mainloop()
