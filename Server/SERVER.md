# Server

This is a Gopher+NLP server written in Python. It is currently a work in progress, and does not function fully, especially given the difficulty in finding exact information on Gopher protocol extensions. 

The server offers a number of AI augmented features. First, it natively supports giap files. Second, it utilizes AI to search identify and describe each item available so that other LLMs can more easily find and utilize them. It does so by traversing the root directory and child directories, scanning each file. Thie initial load can take quite some time if there are a lot of files to scan, but once scanned, the system will pull from cached information unless the item has changed. 