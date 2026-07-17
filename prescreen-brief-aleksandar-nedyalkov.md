# AI-Powered Document Analyzer for Renewable Energy Investments

## Overview
TerraWatt Analytics is a consulting firm that advises investors on renewable energy projects. Their analysts currently spend dozens of hours per week manually reading dense, multi-hundred-page PDF project proposals to extract key financial and technical data points for their evaluation models. This manual process is slow, tedious, and prone to human error, creating a significant bottleneck in their investment pipeline. To solve this, TerraWatt has contracted you to build a prototype service that automates the extraction of structured information from these project proposals.

Your task is to build a full-stack application that allows an analyst to upload a project proposal PDF and receive a structured summary of its key data. The backend service, written in Python, will be responsible for processing the PDF and using a Large Language Model (LLM) to perform the information extraction. You will need to design a reliable extraction process that can handle variations in document layouts and gracefully manage cases where information is missing. The system should expose this functionality via a simple API.

Alongside the backend, you will build a basic web-based frontend. The UI does not need to be polished or visually complex; a functional interface that allows a user to upload a document and clearly view the extracted results is sufficient. We are most interested in your system design, the reliability of your AI-powered extraction logic, your approach to testing, and your thoughts on how such a system would be evaluated and maintained in production.

## Deliverables
- A public GitHub repository or Gist URL containing your complete solution.
- A detailed README.md file explaining your design decisions, trade-offs, setup instructions, and how to run and test the application.
- The Python backend service, including an API for document submission and data retrieval.
- A functional frontend UI (e.g., React, Next.js, or plain HTML/CSS/JS) that consumes the backend API.
- A log or export of your conversations with any AI assistants (e.g., GitHub Copilot Chat, Claude, ChatGPT) used during development, committed to the repository.

## Suggested tools / libraries
- Backend: FastAPI, Flask
- Data Validation: Pydantic
- PDF Processing: pypdf, pdfplumber
- AI/LLM: OpenAI API, Anthropic API, or a local model via Ollama
- AI Frameworks (Optional): LangChain, LlamaIndex
- Frontend: React + Vite, Next.js, or plain HTML/CSS/JavaScript with the Fetch API

## On AI assistants & follow-up
- We expect and encourage you to use documentation, open-source libraries, and AI assistants. The goal is to assess your design judgment, not your memorization skills.
- Be prepared to walk us through your code and explain the rationale behind your architectural decisions and trade-offs during the follow-up interview.
- Please commit a log of your AI assistant conversations to your repository and briefly describe in your README which tools you used and for what parts of the task. This is a required deliverable.
- Focus on building a robust and well-designed core system. A simple, working solution with good foundations is valued more than a complex but fragile one.

## How to submit
Reply to this email with **one** public GitHub repository or gist URL containing your solution.