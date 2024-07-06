"""This program converts the file descriptions in strace -tt -ff outputs into their file paths."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
import re

openat3_re = re.compile(r'openat\(\S+, "(\S+)", (\S+)\)\s+=\s+(\d+)')
openat4_re = re.compile(r'openat\(\S+, "(\S+)", (\S+), \S+\)\s+=\s+(\d+)')
close_re = re.compile(r'close\((\d+)\)')
write_re = re.compile(r'write\((\d+), .+, (\S+)\)\s+=\s+(\d+)')
read_re = re.compile(r'read\((\d+), .+, (\d+)\)\s+=\s+(\d+)')
lseek_re = re.compile(r'lseek\((\d+), (-?\d+), (\S+)\)\s+=\s+(\d+)')
mmap_re = re.compile(r'mmap\(\S+, (\d+), (\S+), (\S+), (\d+), (\S+)\).+')
unlink_re = re.compile(r'unlink\("(\S+)"\)\s+=\s+\d+')

@dataclass
class SysCall:
  pid: str
  path: str
  timestamp: str

@dataclass
class OpenAt3(SysCall):
  flags: str
  pass

@dataclass
class OpenAt4(SysCall):
  flags: str
  pass

@dataclass
class Close(SysCall):
  pass

@dataclass
class Write(SysCall):
  count: int
  ret: int

@dataclass
class Read(SysCall):
  count: str
  ret: str

@dataclass
class LSeek(SysCall):
  offset: str
  whence: str
  ret: str

@dataclass
class MMap(SysCall):
  length: str
  prot: str
  flags: str
  offset: str

@dataclass
class Unlink(SysCall):
  pass

def strace_events(strace_file):
  if not strace_file:
    return []

  # Map of pid -> fd -> path
  fd_paths = defaultdict(lambda: defaultdict(str))

  def lookup_fd(pid, fd):
    if fd == 0:
      return "STDIN"
    if fd == 1:
      return "STDOUT"
    if fd == 2:
      return "STDERR"

    return fd_paths[pid].get(fd, f"({fd})???")

  # Read the strace file line by line
  # Assumes that strace has been run with the -tt -f option
  with open(strace_file, 'r') as strace_f:
    for line in strace_f:
      pid, timestamp, call = line.strip().split(None, 2)

      event = SysCall(pid, call, timestamp)

      openat_match = openat3_re.match(call)
      if openat_match:
        path, flags, fd = openat_match.groups()
        fd_paths[pid][fd] = path
        event = OpenAt3(pid, path, timestamp, flags)

      openat_match = openat4_re.match(call)
      if openat_match:
        path, flags, fd = openat_match.groups()
        fd_paths[pid][fd] = path
        event = OpenAt4(pid, path, timestamp, flags)

      close_match = close_re.match(call)
      if close_match:
        fd = close_match.group(1)
        path = lookup_fd(pid, fd)
        event = Close(pid, path, timestamp)
        if fd in fd_paths[pid]:
          del fd_paths[pid][fd]

      write_match = write_re.fullmatch(call)
      if write_match:
        fd, count, ret = write_match.groups()
        path = lookup_fd(pid, fd)
        event = Write(pid, path, timestamp, count, ret)

      read_match = read_re.fullmatch(call)
      if read_match:
        fd, count, ret = read_match.groups()
        path = lookup_fd(pid, fd)
        event = Read(pid, path, timestamp, count, ret)

      lseek_match = lseek_re.fullmatch(call)
      if lseek_match:
        fd, offset, whence, ret = lseek_match.groups()
        path = lookup_fd(pid, fd)
        event = LSeek(pid, path, timestamp, offset, whence, ret)

      mmap_match = mmap_re.fullmatch(call)
      if mmap_match:
        length, prot, flags, fd, offset = mmap_match.groups()
        path = lookup_fd(pid, fd)
        event = MMap(pid, path, timestamp, length, prot, flags, offset)

      unlink_match = unlink_re.fullmatch(call)
      if unlink_match:
        path = unlink_match.group(1)
        event = Unlink(pid, path, timestamp)

      yield event

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Extract filesystem events from strace log')
  parser.add_argument('strace_file', type=str, help='path to the strace log')

  args = parser.parse_args()

  for e in strace_events(args.strace_file):
    call = ""
    if isinstance(e, OpenAt3) or isinstance(e, OpenAt4):
      call = 'open("{}, {}")'.format(e.path, e.flags)
    elif isinstance(e, Close):
      call = 'close("{}")'.format(e.path)
    elif isinstance(e, Write):
      call = 'write("{}", {}) = {}'.format(e.path, e.count, e.ret)
    elif isinstance(e, Read):
      call = 'read("{}", {}) = {}'.format(e.path, e.count, e.ret)
    elif isinstance(e, LSeek):
      call = 'lseek("{}", {}, {}) = {}'.format(e.path, e.offset, e.whence, e.ret)
    elif isinstance(e, MMap):
      call = 'mmap({}, {}, {}, "{}", {})'.format(e.length, e.prot, e.flags, e.path, e.offset)
    elif isinstance(e, Unlink):
      call = 'unlink("{}")'.format(e.path)
    else:
      call = e.path

    print('\t'.join([e.timestamp, call]))