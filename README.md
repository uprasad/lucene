# Lucene Experiments

## Indexing

### Docker container setup
1. Clone the repository and `cd` into the cloned directory
1. Build the Docker image `$ docker build -t <image-name>`
1. Start a container and connect to it `$ docker run -it test-img /bin/bash`

### Indexing tool
The indexing tool doesn't require arguments
```
/home$ java -cp lucene.jar:lucene-core-9.11.0.jar indexing.IndexData
```

and available arguments can be viewed with the `-help` flag
```
/home$ java -cp lucene.jar:lucene-core-9.11.0.jar indexing.IndexData -help
java indexing.IndexData [-help]
	[-index INDEX_PATH]
	[-num_docs NUM_DOCS]
	[-update]
	[-docs_per_segment DOCS_PER_SEGMENT]
	[-info_stream INFO_STREAM_FILE]
	[-dict DICT_FILE]
	[-disable_compound_file]
```

The invocation can be wrapped in an `strace -tt -f` to dump filesystem trace logs e.g.
```
/home$ mkdir strace_out
/home$ strace -tt -f \
  -e openat,close,read,write,mmap,lseek,unlink \
  -o strace_out/strace.log \
  java -cp lucene-core-9.11.0.jar:lucene.jar indexing.IndexData \ 
  -num_docs 5000 \
  -docs_per_segment 100
```

Filesystem activity during indexing can then be visualized by running
```
/home$ python3 strace_events_viz.py strace_out/strace.log --with_pids
```