"""This program converts the file descriptions in strace -tt -ff outputs into their file paths."""

from collections import defaultdict
from pprint import pprint
import re
import sys

openat3_re = re.compile('openat\(\S+, "(\S+)", \S+\)\s+=\s+(\d+)')
openat4_re = re.compile('openat\(\S+, "(\S+)", \S+, \S+\)\s+=\s+(\d+)')
close_re = re.compile('close\((\d+)\)')
write_re = re.compile('write\((\d+), .+, (\S+)\)\s+=\s+(\d+)')
read_re = re.compile('read\((\d+), .+, (\d+)\)\s+=\s+(\d+)')
lseek_re = re.compile('lseek\((\d+), (-?\d+), (\S+)\)\s+=\s+(\d+)')
mmap_re = re.compile('mmap\(\S+, (\d+), (\S+), (\S+), (\d+), (\S+)\).+')

def main():
  if len(sys.argv) < 2:
    print('Usage: {} <strace_file>'.format(sys.argv[0]))
    sys.exit(1)

  fd_paths = defaultdict(str)
  fd_paths["0"] = "STDIN"
  fd_paths["1"] = "STDOUT"
  fd_paths["2"] = "STDERR"

  # Read the strace file line by line
  # Assumes that strace has been run with the -tt -ff option, so each pid has a separate strace
  with open(sys.argv[1], 'r') as strace_f:
    for line in strace_f:
      timestamp, call = line.strip().split(None, 1)

      openat_match = openat3_re.match(call)
      if openat_match:
        path, fd = openat_match.groups()
        fd_paths[fd] = path

      openat_match = openat4_re.match(call)
      if openat_match:
        path, fd = openat_match.groups()
        fd_paths[fd] = path

      close_match = close_re.match(call)
      if close_match:
        fd = close_match.group(1)
        call = 'close("{}")'.format(fd_paths.get(fd, 'INVALID({})'.format(fd)))
        if fd in fd_paths:
          del fd_paths[fd]

      write_match = write_re.fullmatch(call)
      if write_match:
        fd, count, ret = write_match.groups()
        call = 'write("{}", {}) = {}'.format(fd_paths.get(fd, 'INVALID({})'.format(fd)), count, ret)

      read_match = read_re.fullmatch(call)
      if read_match:
        fd, count, ret = read_match.groups()
        call = 'read("{}", {}) = {}'.format(fd_paths.get(fd, 'INVALID({})'.format(fd)), count, ret)

      lseek_match = lseek_re.fullmatch(call)
      if lseek_match:
        fd, offset, whence, ret = lseek_match.groups()
        call = 'lseek("{}", {}, {}) = {}'.format(fd_paths.get(fd, 'INVALID({})'.format(fd)), offset, whence, ret)

      mmap_match = mmap_re.fullmatch(call)
      if mmap_match:
        length, prot, flags, fd, offset = mmap_match.groups()
        call = 'mmap({}, {}, {}, "{}", {})'.format(length, prot, flags, fd_paths.get(fd, 'INVALID({})'.format(fd)), offset)

      print('\t'.join([timestamp, call]))

if __name__ == '__main__':
  main()