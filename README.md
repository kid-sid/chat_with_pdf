# Chat with your own PDF

You must have came across [chatpdf](www.chatpdf.com) where you can upload your pdf and ask questions to get answers from your PDF file. This repo contains the implementation of a chat bot like chatpdf.com using streamlit as the frontend.

This code contains RAG architecture which takes your PDF texts as the context and provides answers to your queries.

## **Overview of the architecture**

![RAG Architecture](https://github.com/user-attachments/assets/2ef6b915-27d4-4fc0-9d62-6cdce6afd053)

**Architecture:**

Retrieval part of the model helps to retrieve information from the vector store.
Augmented part is the augmentation of the data by adding our own custom data by increasing the knowledge base of the LLM.
Generation part is used for text completion by using the next word prediction capability of the LLM.

All the RAG apps follow more or less same type of architure as above diagram.

Here we are uploading a PDF as the step one.
Then the contents/texts of the PDF are getting extracted from it as the second step.
LLMs can't take all the texts at once due to their context length limitation, so we created chunks out of those text.
Then we created vectors of those chunks and stored it in a vector database, in our case it is FAISS.

Then whenever someone asks a question, LLM answers considering vectors stored in the database as the context.

**Credentials screenshot:**

![Signup/Login page](https://github.com/user-attachments/assets/f56dd4fe-a9e5-4367-9d3b-02ced90dc5a3)

New users need to Signup and then do a login.

**Question answering interface:**

![Chatbot interface](https://github.com/user-attachments/assets/0bb10db0-16a4-4e4b-b905-820f6ee1b463)

Show Query History option will show all the previous queries asked by a user and their answers.
We can use Browse File option for uploading the PDF.
Below text box is for adding your quer and press enter to get the response.







