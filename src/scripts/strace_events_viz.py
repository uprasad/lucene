"""This program visualizes filesystem events in strace logs."""

import argparse
import time
from collections import defaultdict
from strace_events import strace_events, OpenAt3, OpenAt4, Write, Read, LSeek, Close, MMap, SysCall
from tqdm import tqdm

BLOCK_SIZE=8192

def strace_events_viz(strace_file, with_pids=False):
  events = list(strace_events(strace_file, with_pids=with_pids))

  index_events = []
  event_counts = defaultdict(int)
  for e in events:
    if e.path.endswith('pos') or e.path.endswith('.tim') or e.path.endswith('.doc'):
      event_counts[e.path] += 1
      index_events.append(e)

  # Progress bar total is set to the maximum of the number of events for any file
  progress_total = max(event_counts.values())

  # Helper function for pretty-printing descriptions
  def desc(e: SysCall) -> str:
    if with_pids:
      return f"(pid:{e.pid}, ts:{e.timestamp}) {e.path}"
    else:
      return f"(ts:{e.timestamp}) {e.path}"

  path_pos = defaultdict(tqdm)
  for e in index_events:
    if isinstance(e, OpenAt3) or isinstance(e, OpenAt4):
      t = tqdm(
        index_events,
        total=BLOCK_SIZE*progress_total, # Scale up total by BLOCK_SIZE
        unit='off',
        desc=desc(e),
        unit_scale=True,
        bar_format='{desc} {n_fmt} {unit} {bar}',
      )
      # Resume progress if the file is appended
      if 'O_APPEND' in e.flags and e.path in path_pos:
        t.initial = path_pos[e.path].n

      path_pos[e.path] = t
    elif isinstance(e, Write):
      t = path_pos[e.path]
      t.set_description(f"{desc(e)} (w)")
      t.update(int(e.ret))
    elif isinstance(e, Read):
      t = path_pos[e.path]
      t.set_description(f"{desc(e)} (r)")
      t.update(int(e.ret))
    elif isinstance(e, LSeek):
      # Handle lseek whence flag
      if e.whence == 'SEEK_CUR':
        path_pos[e.path].update(int(e.offset))
      elif e.whence == 'SEEK_SET':
        t = path_pos[e.path]
        t.update(int(e.offset)-t.n)
    elif isinstance(e, Close):
      path_pos[e.path].close()
    elif isinstance(e, MMap):
      t = path_pos[e.path]
      t.set_description(f"{desc(e)}, (mmap)")

    time.sleep(0.01)

  # Close all the progress bars
  for t in path_pos.values():
    t.close()

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Extract filesystem events from strace log')
  parser.add_argument('strace_file', type=str, help='path to the strace log')
  parser.add_argument('--with_pids', action='store_true')

  args = parser.parse_args()

  strace_events_viz(args.strace_file, args.with_pids)