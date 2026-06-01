# Shakespeare RAG

### This is the raw plan that I wrote for this project. I fed it into Claude and answered its follow-up questions to write the final project plan doc, which is also in this folder.

Our goal
our app must be able to answer non-trivial questions about shakespeare plays. ex. "what are the themes of hamlet?", "what is the mental state of X character right before they die?"
Our RAG pipeline
* download the raw books online for free
* for each book:
   * each scene of each act is a chunk. we can chunk using a simple regex on ACT/SCENE Markers
   * use `text-embedding-3-small` vector embedding model to encode chunks into vectors
   * store vectors in a pinecone vectorDB
* at runtime:
   * encode user query into a vector
   * semantic look-up of this vector in pinecone
   * find top 3 matching chunks, grab the original scenes
   * append the scenes to the user query
   * wrap the entire thing in a custom prompt. ex. "answer the following query in a pleasant way. here are some scenes from the play to help"
   * run through an LLM `gpt-4o-mini` works
   * give the answer to the user

project structure
a python file that downloads all the plays from gutenberg, stores them in the `plays` folder 
a python file that uses regex to chunk a given play. stores the chunks as txt files in the `chunks` folder
a python file that runs the embedding model, encodes the chunks, stores into a persistent vector DB
a python file that is used by the user at runtime to give them the answer to their questio