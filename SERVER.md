# Gopher+NLP Server

The server offers a number of AI augmented features. First, it natively supports giap files. Second, it utilizes AI to search identify and describe each item available so that other LLMs can more easily find and utilize them. It does so by traversing the root directory and child directories, scanning each file. Thie initial load can take quite some time if there are a lot of files to scan, but once scanned, the system will pull from cached information unless the item has changed. 