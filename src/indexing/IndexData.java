package indexing;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.KeywordField;
import org.apache.lucene.document.TextField;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.index.IndexWriterConfig.OpenMode;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.InfoStream;
import org.apache.lucene.util.PrintStreamInfoStream;

class IndexData {
  static final int SENTENCE_LENGTH = 100;

  public static void main(String[] args) throws IllegalArgumentException {
    String indexPath = "index";
    int numDocs = (int) 1e5;
    int docsPerSegment = (int) 1e5;
    boolean update = false;
    String infoStreamFile = null;
    String dictFile = "/usr/share/dict/words";
    boolean useCompoundFile = true;

    // Parse command-line arguments
    for (int i=0; i<args.length; i++) {
      switch (args[i]) {
        case "-index":
          indexPath = args[++i];
          break;
        case "-num_docs":
          numDocs = Integer.parseInt(args[++i]);
          break;
        case "-docs_per_segment":
          docsPerSegment = Integer.parseInt(args[++i]);
          break;
        case "-update":
          update = true;
          break;
        case "-info_stream":
          infoStreamFile = args[++i];
          break;
        case "-dict":
          dictFile = args[++i];
          break;
        case "-disable_compound_file":
          useCompoundFile = false;
          break;
        case "-help":
          System.out.println(usage());
          System.exit(0);
        default:
          throw new IllegalArgumentException("unsupported parameter " + args[i]);
      }
    }

    Directory indexDir = null;
    try{
      indexDir = FSDirectory.open(Paths.get(indexPath));
    } catch (IOException e) {
      System.out.println("Error opening directory " + indexPath + ": " + e.getMessage());
      System.exit(1);
    }

    // Read dictionary words
    List<String> dict = new ArrayList<>();
    try {
      dict = Files.readAllLines(Paths.get(dictFile));
    } catch (IOException e) {
      System.out.println("Dictionary words file " + dictFile + " not found: " + e.getMessage());
    }
    System.out.println("Read " + dict.size() + " dictionary words");

    // Set a custom info stream if specified
    InfoStream infoStream = InfoStream.NO_OUTPUT;
    if (infoStreamFile != null) {
      try {
        infoStream = new PrintStreamInfoStream(new PrintStream(infoStreamFile));
      } catch (FileNotFoundException e) {
        System.out.println("Error opening info stream on file " + infoStreamFile + ": " + e.getMessage());
      }
    }

    // Defaults: standard analyzer
    IndexWriterConfig iwc = new IndexWriterConfig();
    iwc.setUseCompoundFile(useCompoundFile);
    iwc.setMaxBufferedDocs(docsPerSegment);
    // Set a really high (1GB) RAM buffer so we hit the document buffer limit first
    iwc.setRAMBufferSizeMB(1 << 30);
    iwc.setInfoStream(infoStream);
    iwc.setOpenMode(OpenMode.CREATE);
    if (update) {
      iwc.setOpenMode(OpenMode.CREATE_OR_APPEND);
    }

    Date start = new Date();
    try (IndexWriter writer = new IndexWriter(indexDir, iwc)) {
      IndexData indexData = new IndexData();
      indexData.indexDocs(writer, numDocs, dict);
    } catch (IOException e) {
      System.out.println("Error indexing documents to " + indexPath + ": " + e.getMessage());
      System.exit(1);
    }

    Date end = new Date();
    try (IndexReader reader = DirectoryReader.open(indexDir)) {
      System.out.println("Num docs: " + reader.numDocs());
      System.out.println("Deleted docs: " + reader.numDeletedDocs());
      System.out.println("Duration (ms): " + (end.getTime() - start.getTime()));
    } catch (IOException e) {
      System.out.println("Error reading from " + indexPath + ": " + e.getMessage());
      System.exit(1);
    }
  }

  private static String usage() {
    return "java indexing.IndexData [-help]\n"
    + "\t[-index INDEX_PATH]\n"
    + "\t[-num_docs NUM_DOCS]\n"
    + "\t[-update]\n"
    + "\t[-docs_per_segment DOCS_PER_SEGMENT]\n"
    + "\t[-info_stream INFO_STREAM_FILE]\n"
    + "\t[-dict DICT_FILE]\n"
    + "\t[-disable_compound_file]";
  }

  private void indexDocs(IndexWriter writer, int numDocs, List<String> dict) throws IOException {
    for (int i=0; i<numDocs; i++) {
      // Generate a random sentence
      List<String> sentence = new ArrayList<>();
      for (int j=0; j<SENTENCE_LENGTH; ++j) {
        int index = (int) (Math.random() * dict.size());
        sentence.add(dict.get(index));
      }

      // Build a document
      String docID = String.valueOf(i);
      Document doc = new Document();
      doc.add(new KeywordField("id", docID, Field.Store.YES));
      doc.add(new TextField("sentence", String.join(" ", sentence), Field.Store.NO));

      // Add or update document
      if (writer.getConfig().getOpenMode() == OpenMode.CREATE) {
        writer.addDocument(doc);
      } else {
        writer.updateDocument(new Term("id", docID), doc);
      }
    }
  }
}