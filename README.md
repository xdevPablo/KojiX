<p align="center">
  <img src="assets/logo.png" width="500"/>
  <br/>
<h1 align="center">KojiX</h1>
<p align="center">
  Autonomous Cyber Threat Intelligence Engine  
</p>

<p align="center">
  <b>AI-Powered OSINT & Vulnerability Analysis Dashboard</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-active-success" />
  <img src="https://img.shields.io/badge/python-3.9+-blue" />
  <img src="https://img.shields.io/badge/build-nuitka-orange" />
  <img src="https://img.shields.io/badge/TLP-AMBER-ff8c00" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
</p>

---

## 📚 Table of Contents

- [Overview](#-overview)
- [Demonstration](#-demonstration)
- [Key Capabilities](#-key-capabilities)
- [Technical Architecture](#-technical-architecture)
- [Technical Stack](#-technical-stack)
- [Sample Output](#-sample-output)
- [Project Structure](#-project-structure)
- [Setup & Installation](#-setup--installation)
- [Configuration](#-configuração-env)
- [Build](#-compilação-com-nuitka)
- [Roadmap](#-roadmap)
- [Security & Ethics](#-security--ethics)
- [Contributing](#-contributing)
- [Developer](#-developer)

---

## ⬩➤ Overview

KojiX é uma engine de Cyber Threat Intelligence (CTI) projetada para automatizar a coleta, correlação e síntese estratégica de ameaças cibernéticas.

A ferramenta utiliza processamento assíncrono para minerar dados do Reddit e da base NVD/NIST, processando-os por meio de agentes de IA (Google Gemini) para gerar dossiês técnicos de alta densidade.

---

## 🎥 Demonstration

### Interface (GUI)
<p align="center">
  <img src="assets/gui.png" width="800"/>
</p>

### CLI
<p align="center">
  <img src="assets/cli.png" width="800"/>
</p>

### Report
<p align="center">
  <img src="assets/report.png" width="800"/>
</p>

---

## 🚀 Key Capabilities

- **Dual-Mode Interface**  
  GUI moderna + CLI para operações rápidas

- **Multi-Source Intelligence**  
  - Reddit OSINT (IoCs, leaks, discussões técnicas)  
  - Integração NVD/NIST (CVE + severity)

- **AI Strategic Pipeline**  
  - Recon Agent → Vetores de ataque  
  - Quant Agent → Análise quantitativa  
  - Strat Agent → Estratégia e mitigação  

- **Async Performance**  
  Arquitetura baseada em `asyncio` e `aiohttp`

- **Standalone Deployment**  
  Build em `.exe` único via Nuitka

---

## 🧩 Technical Architecture

| Fase | Operação | Output |
|------|----------|--------|
| COLLECT | Reddit + NVD | Raw Data |
| RECON | Filtragem | Attack Vectors |
| ANALYTICS | Correlação | Severity |
| STRATEGY | IA | Mitigation |
| REPORT | Geração | PDF |

---

## ⚙️ Technical Stack

- Python 3.9+  
- CustomTkinter (GUI)  
- Google Gemini (AI Engine)  
- aiohttp + BeautifulSoup4  
- SQLite (cache)  
- FPDF2 + Markdown  
- Nuitka (compilação)

---

## 📄 Sample Output

```json
{
  "threat": "CVE-2024-XXXX",
  "severity": "Critical",
  "vector": "Remote Code Execution",
  "source": "Reddit + NVD Correlation",
  "recommendation": "Immediate patching and network isolation"
}
```

---

## 📂 Project Structure

```
KojiX/
├── assets/
├── core/
├── agents/
├── reports/
├── utils/
├── launcher.py
├── requirements.txt
└── .env
```

---

## 🛠️ Setup & Installation

### Pré-requisitos

- Python 3.9+  
- Gemini API Key  
- NVD API Key (opcional)

### Instalação

```bash
git clone https://github.com/xdevPablo/KojiX.git
cd KojiX
python -m venv .venv
```

### Ativar ambiente

**Windows:**
```powershell
.venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### Instalar dependências

```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuração (.env)

```env
GEMINI_API_KEY=your_key_here
NVD_API_KEY=your_key_here
```

---

## 🧩 Compilação com Nuitka

### Windows

```bash
python -m nuitka --standalone --onefile ^
  --windows-disable-console ^
  --include-data-dir=assets=assets ^
  --enable-plugin=tk-inter ^
  launcher.py
```

### Linux / macOS

```bash
python -m nuitka --standalone --onefile \
  --include-data-dir=assets=assets \
  --enable-plugin=tk-inter \
  launcher.py
```

---

## 🗺️ Roadmap

- [x] Reddit OSINT integration  
- [x] Gemini AI pipeline  
- [x] PDF report generation  
- [ ] Web dashboard  
- [ ] API pública  
- [ ] Integração com novas fontes (X, Telegram)

---

## 🔐 Security & Ethics

### TLP Compliance
Compatível com **TLP:AMBER**

### Ethical Use
Uso exclusivo para:
- Pesquisa  
- Defesa cibernética  
- Fins acadêmicos  

Uso indevido é de responsabilidade do usuário.

---

## 🤝 Contributing

Pull requests são bem-vindos. Para mudanças maiores, abra uma issue primeiro.

---

## 👨‍💻 Developer

**Pablo Guerra**  
Computer Science Student  

Interesses:
- Full-Stack  
- Automação  
- Sistemas & Engines  

📍 Joinville, SC — Brasil  

---

<p align="center">
  Built with focus on performance, intelligence and automation.
</p>
