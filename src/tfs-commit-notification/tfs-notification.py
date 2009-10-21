from threading import Thread
from config import agents

import cmd
import sys


class CLI(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = ''

    def preloop(self):
        print "Enter 'q' to quit"

    def do_q(self, args):
        sys.exit(1)

def run_cli():
    c = CLI()
    c.cmdloop()

if __name__ == '__main__':
    for agent in agents:
        agent.start()

    cli = Thread(target=run_cli)
    cli.start()
