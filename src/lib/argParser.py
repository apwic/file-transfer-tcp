import argparse as ap

class ArgParserServer:

  def __init__(self):
    self.parser = ap.ArgumentParser(description="Server for file transfer using UDP protocol")
    self.parser.add_argument("port", type=int, help="Port number")
    self.parser.add_argument("path", type=str, help="Path to file")

  def parse(self):
    return self.parser.parse_args()

class ArgParserClient:
  
    def __init__(self):
      self.parser = ap.ArgumentParser(description="Client for file transfer using UDP protocol")
      self.parser.add_argument("port", type=int, help="Port number")
      self.parser.add_argument("dest", type=int, help="Destination port number")
      self.parser.add_argument("path", type=str, help="Output path file")
  
    def parse(self):
      return self.parser.parse_args()