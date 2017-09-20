"""
This file is part of Sardana-Training documentation 
2017 ALBA Synchrotron

Sardana-Training documentation is free software: you can redistribute it and/or 
modify it under the terms of the GNU Lesser General Public License as published 
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Sardana-Training documentation is distributed in the hope that it will be 
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Sardana-Training.  If not, see <http://www.gnu.org/licenses/>.
"""


import random
import socket
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import mpl_toolkits.mplot3d.axes3d as p3

from threading import Lock
from threading import Thread

class SocketListenerThread(Thread):
    def __init__(self, serversock):
        Thread.__init__(self)
        self.serversock = serversock
        self.serve = True
        self.clientsock = None

    def run(self):
        while self.serve:
            try:
                self.clientsock, addr = self.serversock.accept()
                try:
                    while True:
                        data = self.clientsock.recv(4096)
                        if data == '': break
                        ans = self.parse_cmd(data.lower().strip())
                        self.clientsock.send(ans)
                except Exception,e:
                    pass # forced by a socket shutdown
            except Exception,e:
                pass # forced by a socket shutdown

    def parse_cmd(self, cmd):
        ans = 'NOK:'+cmd
        if cmd == 'clear':                          # CLEAR will erase the plot
            with lock:
                global x, y, z
                x = [motor_positions[0]]
                y = [motor_positions[1]]
                z = [motor_positions[2]]
            ans = 'OK:'+cmd+':cleared'
        
        return ans+'\n'

    def shutdown(self):
        if self.clientsock is not None:
            self.clientsock.shutdown(0)
        self.serve = False
        self.serversock.shutdown(0)


class UpdatePositionsThread(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.stop_loop = False
    def run(self):
        while not self.stop_loop:
            update_positions()

def update_positions():
    for i in range(3):
        with lock:
            motor_positions[i] = random.random()*200 - 100

global x,y,z,lock,motor_positions
lock = Lock()
motor_positions = [0,0,0]

fig = plt.figure()
ax = p3.Axes3D(fig)

MAX_POINTS=100
xmax=1000
x = [motor_positions[0]]
y = [motor_positions[1]]
z = [motor_positions[2]]

point, = ax.plot([x[0]], [y[0]], [z[0]], 'o')
line, = ax.plot(x, y, z, label='x-y-z-trajectory')

ax.legend()
ax.set_xlim([-100, 100])
ax.set_ylim([-100, 100])
ax.set_zlim([-100, 100])

def update(i):
    with lock:
        if len(x) == MAX_POINTS:
            x.pop(0)
            y.pop(0)
            z.pop(0)
        x.append(motor_positions[0])
        y.append(motor_positions[1])
        z.append(motor_positions[2])
    point.set_data((x[-1], y[-1]))
    point.set_3d_properties(z[-1], 'z')
    line.set_data(x,y)
    line.set_3d_properties(z, 'z')


if __name__ == '__main__':
    ADDR = ('127.0.0.1', 5000)
    serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversock.bind(ADDR)
    serversock.listen(1)
    slt = SocketListenerThread(serversock)
    slt.start()
    
    upt = UpdatePositionsThread()
    upt.start()
    a = anim.FuncAnimation(fig, update, frames=xmax, repeat=True, interval=50)
    plt.show()
    upt.stop_loop = True
    slt.shutdown()


