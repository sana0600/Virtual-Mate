# 🤖 VirtualMate

VirtualMate is an AI-powered task assistant. Give it a plain-English task and it either:

- **Chats** - answers simple questions by researching the web and summarizing the results, or
- **Acts as an agent** - breaks the task into steps (plan → research → draft → generate) and produces real output: a PDF, Word document, Excel sheet, or a drafted email, ready to download.

Built with **FastAPI** on the backend and a lightweight **HTML/CSS/JS** frontend, powered by **Groq's GPT-OSS 120B** model via LangChain.

## ✨ Features

- Automatic **intent detection** - routes a task to chat mode or agent mode
- **Web research** via DuckDuckGo search, summarized by the LLM
- **Document generation**: PDF, DOCX, and XLSX output
- **Email drafting**
- Simple single-page frontend with live status indicator

## 🧱 Tech Stack

| Layer      | Tech |
|------------|------|
| Backend    | FastAPI, Uvicorn, Pydantic |
| AI / LLM   | LangChain + Groq (`openai/gpt-oss-120b`) |
| Search     | `ddgs` (DuckDuckGo Search) |
| Documents  | `python-docx`, `openpyxl`, ReportLab |
| Frontend   | HTML, CSS, vanilla JavaScript |

## 📁 Project Structure

```
Virtual-Mate/
├── backend/
│   ├── main.py                # FastAPI app & routes
│   ├── agents/
│   │   ├── planner.py         # Breaks a task into steps (LLM)
│   │   └── executor.py        # Executes each planned action
│   ├── tools/
│   │   ├── web_search.py      # DuckDuckGo search
│   │   ├── summarizer.py      # LLM summarization
│   │   ├── email_tool.py      # Email draft generation
│   │   └── document_tool.py   # PDF / DOCX / XLSX generation
│   ├── generated/             # Output files (created at runtime, gitignored)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html
    └── static/
        ├── app.js
        ├── styles.css
        └── images/
```

## 🚀 Getting Started (Local)

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com/keys)

### Setup

```bash
git clone https://github.com/<your-username>/virtual-mate.git
cd virtual-mate

python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r backend/requirements.txt

cp backend/.env.example backend/.env  # then paste your GROQ_API_KEY into .env
```

### Run

```bash
uvicorn backend.main:app --reload
```

Visit **http://127.0.0.1:8000** in your browser.

## 🔐 Environment Variables

| Variable        | Description                          |
|-----------------|---------------------------------------|
| `GROQ_API_KEY`  | Your Groq API key (get one for free at console.groq.com) |
| `GROQ_MODEL`    | Groq model ID; defaults to `openai/gpt-oss-120b` |

The UI checks `/health` and shows the API as ready only when required configuration is present.

## ✅ Tests

```bash
python3 -m pytest -q backend/tests
```

Never commit your real `.env` file - only `.env.example` is tracked in this repo.

## 🌍 Live Demo

[https://virtual-mate-z4xr.onrender.com]
[https://huggingface.co/spaces/sana0600/Virtual-Mate]

## 📄 License

MIT - feel free to fork and build on this.
