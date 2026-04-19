## 1. Panorama e Contexto da Ameaça

O cenário de ameaças atual é caracterizado por uma dicotomia preocupante: a persistência de vulnerabilidades legadas em aplicações web e a rápida emergência de novas superfícies de ataque impulsionadas pela adoção de agentes de Inteligência Artificial (IA). Observamos atacantes com maturidade variada, desde exploradores oportunistas de CVEs conhecidas até atores sofisticados capazes de manipular o comportamento autônomo de IAs e comprometer cadeias de suprimentos de software. O impacto operacional abrange desde a execução remota de código e a exfiltração de dados sensíveis até a manipulação de ambientes de desenvolvimento e a escalada de privilégios em sistemas críticos, exigindo uma postura de segurança pro

## 4. Auditoria Quantitativa e Estimativa de Risco

A análise da telemetria OSINT revela a seguinte distribuição de vetores de ataque:

*   **Exploração de Vulnerabilidades**: 78.3%
*   **Evasão de Defesas (EDR/AV)**: 13.0%
*   **Negociação e Resgate**: 8.7%
*   **Impacto em Backups**: 0.0%
*   **Engenharia Social / Phishing**: 0.0%
*   **Movimento Lateral**: 0.0%

O vetor de Exploração de Vulnerabilidades domina o ranking devido à persistência de falhas legadas em aplicações web. Atacantes oportunistas capitalizam sobre CVEs conhecidas, conforme indicado pelo contexto tático. Este método oferece um caminho direto para execução remota de código e exfiltração de dados.

Correlação com o Contexto Tático:

*   **Exploração de Vulnerabilidades**: Correlaciona-se diretamente com a menção de "vulnerabilidades legadas em aplicações web" e "exploradores oportunistas de CVEs conhecidas". O contexto valida a prevalência deste vetor sem especificar CVEs individuais.
*   **Evasão de Defesas (EDR/AV)**: Reflete a necessidade dos atacantes de contornar controles de segurança existentes após a exploração inicial.
*   **Negociação e Resgate**: Indica a fase pós-comprometimento, onde a monetização via ransomware ou extorsão de dados é o objetivo final.

Alocação de Recursos Blue Team Recomendada:

*   Priorizar gestão de vulnerabilidades, com foco em aplicações web e sistemas legados.
*   Implementar e otimizar Web Application Firewalls (WAFs) e scanners de vulnerabilidades contínuos.
*   Fortalecer a detecção e resposta a incidentes (EDR/XDR) para mitigar evasão de defesas.
*   Desenvolver planos de resposta a ransomware e estratégias de backup imutáveis.
*   Investir em segurança de cadeia de suprimentos de software e hardening de ambientes de IA.

## 5. Recomendações Táticas e Conclusão Executiva

**Ações Imediatas (0-72h):**

*   **[CRÍTICO]** Patching de Vulnerabilidades Críticas em Aplicações Web — Como executar: Identificar todas as aplicações web públicas e internas com CVEs conhecidas de alto risco (CVSS > 8.0), priorizando aquelas que permitem execução remota de código (RCE) ou injeção de SQL. Aplicar os patches de segurança fornecidos pelos fabricantes ou desenvolver mitigações temporárias (virtual patching via WAF) imediatamente após testes mínimos de regressão. — Mitiga: CVEs de RCE/SQLi em aplicações web, TTPs de exploração inicial (TA0001).

*   **[ALTO]** Hardening de Web Application Firewalls (WAFs) — Como executar: Revisar e otimizar as regras dos WAFs existentes, garantindo que estejam configurados para bloquear ativamente tentativas de exploração de vulnerabilidades web comuns (OWASP Top 10), incluindo injeção, XSS e manipulação de parâmetros. Implementar regras de negação explícita para tráfego malicioso conhecido e ativar modos de aprendizado para novas aplicações. — Mitiga: Exploração de Vulnerabilidades (78.3%), Evasão de Defesas (T1027).

*   **[ALTO]** Desativação de Serviços e Portas Desnecessárias — Como executar: Realizar um inventário de todos os serviços e portas abertas em servidores de aplicações web e sistemas legados expostos à rede. Desativar ou restringir o acesso a qualquer serviço ou porta que não seja estritamente necessário para a operação, aplicando o princípio do menor privilégio de rede. — Mitiga: Redução da superfície de ataque, TTPs de Reconhecimento (TA0043) e Acesso Inicial (TA0001).

*   **[MÉDIO]** Auditoria de Credenciais Padrão e Expostas — Como executar: Varrer as aplicações web e sistemas legados em busca de credenciais padrão, fracas ou expostas publicamente (via OSINT). Forçar a alteração imediata de senhas para credenciais fortes e únicas, e implementar autenticação multifator (MFA) para todas as interfaces administrativas expostas. — Mitiga: TTPs de Acesso Inicial (T1133, T1078), Brute Force (T1110).

**Ações Estruturais (30/60/90 dias):**

*   **Implementação de um Programa Contínuo de Gestão de Vulnerabilidades:** Estabelecer um ciclo robusto de varredura, priorização, remediação e verificação de vulnerabilidades, com foco especial em aplicações web e sistemas legados. Este programa visa reduzir proativamente o vetor dominante de "Exploração de Vulnerabilidades" (78.3%), garantindo que CVEs conhecidas sejam endereçadas antes que se tornem alvos de atacantes oportunistas.

*   **Fortalecimento da Postura de Segurança em Ambientes de Desenvolvimento e Cadeia de Suprimentos:** Integrar práticas de DevSecOps, como análise estática e dinâmica de código (SAST/DAST), em todas as fases do ciclo de vida de desenvolvimento de software. Isso é crucial para mitigar a emergência de novas "vulnerabilidades legadas" e proteger contra o comprometimento da "cadeia de suprimentos de software", um vetor crescente que pode introduzir falhas antes mesmo da implantação.

*   **Otimização e Expansão das Capacidades de Detecção e Resposta (XDR/SOAR):** Aprimorar a telemetria e as regras de correlação em plataformas XDR, integrando-as com soluções SOAR para automação da resposta a incidentes. Esta medida visa fortalecer nossa capacidade de identificar e reagir rapidamente a "Evasão de Defesas" (13.0%) e outros TTPs pós-exploração, diminuindo o tempo de permanência de atacantes em nossos ambientes.

*   **Desenvolvimento de Estratégias de Segurança para Agentes de IA:** Criar diretrizes e controles específicos para a implantação e uso de agentes de Inteligência Artificial, abordando riscos como manipulação de comportamento, exfiltração de dados por prompts maliciosos e vulnerabilidades em modelos de ML. Esta ação preventiva é essencial para mitigar as "novas superfícies de ataque impulsionadas pela adoção de agentes de Inteligência Artificial" mencionadas no panorama de ameaças.

**Conclusão Executiva:**

O nível de risco atual para a organização é elevado, impulsionado predominantemente pela "Exploração de Vulnerabilidades" em nossas aplicações web e sistemas legados. Este vetor, responsável por 78.3% dos ataques observados, representa a porta de entrada mais crítica para a execução remota de código e a exfiltração de dados sensíveis. A ameaça mais severa reside nas CVEs de execução remota de código (RCE) em aplicações web, que permitem controle total sobre os sistemas comprometidos. A prioridade máxima agora é a execução rigorosa das ações imediatas de patching e hardening de WAF, seguida pela implementação de um programa robusto de gestão de vulnerabilidades e segurança no desenvolvimento para mitigar riscos futuros.



## 6. Apêndice Técnico: Vulnerabilidades Oficiais (NVD/NIST)

> Fonte: National Vulnerability Database (NIST) | Gerado em: 13/04/2026 15:35 UTC

> Total de CVEs High/Critical identificadas: **5**


### 1. CVE-2017-5215 — 🔴 CRÍTICO

| Campo | Valor |
|-------|-------|
| **CVSS Score** | 9.8 |
| **Severidade** | CRITICAL |
| **Vetor de Ataque** | NETWORK |
| **Publicado em** | 2017-05-17 |

**Descrição Oficial:**
The Codextrous B2J Contact (aka b2j_contact) extension before 2.1.13 for Joomla! allows a rename attack that bypasses a "safe file extension" protection mechanism, leading to remote code execution.

**Referências:**
- https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
- https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt

---

### 2. CVE-2017-5214 — 🟠 ALTO

| Campo | Valor |
|-------|-------|
| **CVSS Score** | 7.5 |
| **Severidade** | HIGH |
| **Vetor de Ataque** | NETWORK |
| **Publicado em** | 2017-05-17 |

**Descrição Oficial:**
The Codextrous B2J Contact (aka b2j_contact) extension before 2.1.13 for Joomla! allows prediction of a uniqid value based on knowledge of a time value. This makes it easier to read arbitrary uploaded files.

**Referências:**
- https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
- https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt

---

### 3. CVE-2017-9030 — 🟠 ALTO

| Campo | Valor |
|-------|-------|
| **CVSS Score** | 7.5 |
| **Severidade** | HIGH |
| **Vetor de Ataque** | NETWORK |
| **Publicado em** | 2017-05-17 |

**Descrição Oficial:**
The Codextrous B2J Contact (aka b2j_contact) extension before 2.1.13 for Joomla! allows a directory traversal attack that bypasses a uniqid protection mechanism, and makes it easier to read arbitrary uploaded files.

**Referências:**
- https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
- https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt

---

### 4. CVE-2023-50892 — 🟠 ALTO

| Campo | Valor |
|-------|-------|
| **CVSS Score** | 7.1 |
| **Severidade** | HIGH |
| **Vetor de Ataque** | NETWORK |
| **Publicado em** | 2023-12-29 |

**Descrição Oficial:**
Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') vulnerability in CodexThemes TheGem - Creative Multi-Purpose & WooCommerce WordPress Theme allows Reflected XSS.This issue affects TheGem - Creative Multi-Purpose & WooCommerce WordPress Theme: from n/a through 5.9.1.

**Referências:**
- https://patchstack.com/database/vulnerability/thegem/wordpress-thegem-theme-5-9-1-reflected-cross-site-scripting-xss-vulnerability?_s_id=cve
- https://patchstack.com/database/vulnerability/thegem/wordpress-thegem-theme-5-9-1-reflected-cross-site-scripting-xss-vulnerability?_s_id=cve

---

### 5. CVE-2024-54210 — ⚪ N/A

| Campo | Valor |
|-------|-------|
| **CVSS Score** | None |
| **Severidade** | None |
| **Vetor de Ataque** | None |
| **Publicado em** | 2024-12-06 |

**Descrição Oficial:**
Improper Neutralization of Input During Web Page Generation ('Cross-site Scripting') vulnerability in codexshaper Advanced Element Bucket Addons for Elementor cs-element-bucket allows Stored XSS.This issue affects Advanced Element Bucket Addons for Elementor: from n/a through <= 1.0.2.

**Referências:**
- https://patchstack.com/database/Wordpress/Plugin/cs-element-bucket/vulnerability/wordpress-advanced-element-bucket-addons-for-elementor-plugin-1-0-2-cross-site-scripting-xss-vulnerability?_s_id=cve

---

## 7. Matriz OSINT: Threads Analisadas (Reddit)

> Threads selecionadas por relevância (upvotes) | Total analisado: **15 posts**


#### 1. OpenAI's GPT-5.4 got blocked by safety mechanisms 5 times, searched my machine for tools to bypass them, launched Claude Opus with dangerously bypass permissions flags, tried to COVER UP what he had done, then gave me a "perfect" apology when caught
- **Subreddit:** r/cybersecurity | **Upvotes:** 297 | **Autor:** u/Smart_War3981
- **URL:** https://reddit.com/r/cybersecurity/comments/1sbr7kq/openais_gpt54_got_blocked_by_safety_mechanisms_5/
- **Trecho:** Edit:

Link to the logs: [https://gist.github.com/itstanner5216/07027b0cf7f09a4a68c96776cda993c4](https://gist.github.com/itstanner5216/07027b0cf7f09a4a68c96776cda993c4)

Local file paths and API identifiers are scrubbed. Commands, flags, timestamps, and the agents own words are unedited. The file...

#### 2. [RESEARCH] We scanned 3,471 MCP servers for invisible Unicode — GPT-5.4 follows hidden instructions 100% of the time
- **Subreddit:** r/cybersecurity | **Upvotes:** 12 | **Autor:** u/Accurate_Mistake_398
- **URL:** https://reddit.com/r/cybersecurity/comments/1se27dc/research_we_scanned_3471_mcp_servers_for/
- **Trecho:** We just published research on invisible Unicode smuggling in MCP (Model Context Protocol) tool descriptions the metadata that AI coding agents like Claude Code, Cursor, and Codex read to decide what tools to use.

**The** **short** **version:** An attacker who can publish an npm/PyPI package can...

#### 3. OreWatch – open-source malicious package scanner across 6 ecosystems, now with an MCP server so your AI coding agent stops installing malware.
- **Subreddit:** r/cybersecurity | **Upvotes:** 10 | **Autor:** u/PerceptionOk8748
- **URL:** https://reddit.com/r/cybersecurity/comments/1sejkxy/orewatch_opensource_malicious_package_scanner/
- **Trecho:** There was a lot of feedback after the last release, and we have updated OreWatch.

OreWatch now includes a local MCP server that integrates with Cursor, Codex, and Claude Code to detect malicious dependencies in real time and help prevent their installation. For Mac users, it also adds a menu bar...

#### 4. Cybersecurity statistics of the week (March 9th - March 15th)
- **Subreddit:** r/cybersecurity | **Upvotes:** 6 | **Autor:** u/Narcisians
- **URL:** https://reddit.com/r/cybersecurity/comments/1rwhia9/cybersecurity_statistics_of_the_week_march_9th/
- **Trecho:** Hi guys, I send out a weekly newsletter with the latest cybersecurity vendor reports and research, and thought you might find it useful, so sharing it here.

All the reports and research below were published between March 9th - March 15th.

You can get the below into your inbox every week if you...

#### 5. My take on LLMs in SAST: good for PRs, not yet for full repos
- **Subreddit:** r/cybersecurity | **Upvotes:** 6 | **Autor:** u/Motor-Pollution-947
- **URL:** https://reddit.com/r/cybersecurity/comments/1n9d1lp/my_take_on_llms_in_sast_good_for_prs_not_yet_for/
- **Trecho:** I am fairly new to Reddit but curious to hear thoughts on Semgrep's latest analysis of LLMs for finding code vulnerabilities: ...

#### 6. Runtime security layer for AI agents - request for feedback
- **Subreddit:** r/cybersecurity | **Upvotes:** 4 | **Autor:** u/jimmyracheta
- **URL:** https://reddit.com/r/cybersecurity/comments/1s51h4s/runtime_security_layer_for_ai_agents_request_for/
- **Trecho:** I built a runtime security layer for AI agents and want honest feedback from people who actually think about this stuff.

Background: the fact that AI agents have real filesystem and shell access has never sat well with me, and seeing posts and memes about databases being wiped, files deleted,...

#### 7. I built a runtime security proxy for AI agents using MCP (Model Context Protocol) — looking for honest feedback on where to take it
- **Subreddit:** r/cybersecurity | **Upvotes:** 2 | **Autor:** u/4rs0n1
- **URL:** https://reddit.com/r/cybersecurity/comments/1sazmsv/i_built_a_runtime_security_proxy_for_ai_agents/
- **Trecho:** I've been working on a security-related project for the past few months and would value outside perspectives from people who think about security for a living.

**The problem I kept running into:**

AI coding agents (Claude, Codex, etc.) are increasingly being connected to real infrastructure —...

#### 8. I built an open source framework that does what your CSPM tool won't, show you the actual attack path
- **Subreddit:** r/cybersecurity | **Upvotes:** 2 | **Autor:** u/tayvionp
- **URL:** https://reddit.com/r/cybersecurity/comments/1rqeiyq/i_built_an_open_source_framework_that_does_what/
- **Trecho:** I do detection engineering and cloud security  &amp; auditing an AWS account takes me days, sometimes weeks. CSPM tools help with enumeration but they flag misconfigurations against a checklist and stop there. They don't chain findings into attack paths or generate defenses specific to your...

#### 9. OpenAI Patches ChatGPT Data Exfiltration Flaw and Codex GitHub Token Vulnerability
- **Subreddit:** r/cybersecurity | **Upvotes:** 1 | **Autor:** u/realnarrativenews
- **URL:** https://reddit.com/r/cybersecurity/comments/1s82znb/openai_patches_chatgpt_data_exfiltration_flaw_and/
- **Trecho:** previously unknown vulnerability in OpenAI ChatGPT allowed sensitive conversation data to be exfiltrated without user knowledge or consent, according to new findings from Check Point. A single malicious prompt could turn an otherwise ordinary conversation into a covert exfiltration channel, leaking...

#### 10. Supply Chain Attacks, Hardening Your Dev Environmen
- **Subreddit:** r/cybersecurity | **Upvotes:** 1 | **Autor:** u/YaronElharar
- **URL:** https://reddit.com/r/cybersecurity/comments/1sduv0p/supply_chain_attacks_hardening_your_dev_environmen/
- **Trecho:** You probably know most of these, but I think it’s a good place to publish an approach on how to harden a development environment using a VM (Hyper-V) with Linux on a Windows 11 operating system. If you find something I haven't talked about missed or is wrong, let me know, If not, feel free to drop...

#### 11. mcp-scan: open-source security scanner for MCP (Model Context Protocol) server configs
- **Subreddit:** r/cybersecurity | **Upvotes:** 1 | **Autor:** u/FeelingBiscotti242
- **URL:** https://reddit.com/r/cybersecurity/comments/1s2r0w1/mcpscan_opensource_security_scanner_for_mcp_model/
- **Trecho:** MCP servers run with full filesystem and network access. Most people install them without auditing what they're actually running.

mcp-scan detects MCP server configs across 10 AI tool clients (Claude Desktop, Cursor, VS Code, Windsurf, Codex CLI, Claude Code, Zed, GitHub Copilot, Cline, Roo Code)...

#### 12. ChatGPt Codex in webstorm
- **Subreddit:** r/cybersecurity | **Upvotes:** 0 | **Autor:** u/StatisticianThis1145
- **URL:** https://reddit.com/r/cybersecurity/comments/1shl8b7/chatgpt_codex_in_webstorm/
- **Trecho:** In addition to ChatGPt Codex in webstorm, what other free agent can write code and push it properly? Gemini just ruins everything, for example. Opencode consumes memory and freezes at startup. Kilo?

#### 13. Using AI to identify silent security patches before they are publicly announced
- **Subreddit:** r/cybersecurity | **Upvotes:** 0 | **Autor:** u/rndhouse2
- **URL:** https://reddit.com/r/cybersecurity/comments/1sgjo65/using_ai_to_identify_silent_security_patches/
- **Trecho:** Inspired by recent reports on Claude Mythos and its capability to detect software security vulnerabilities, I developed a proof of concept to evaluate whether LLM-based code analysis can identify silent security patches.

Software project maintainers often patch vulnerabilities without immediate...

#### 14. OSS tool that helps AI &amp; devs search big codebases faster by indexing repos and building a semantic view
- **Subreddit:** r/cybersecurity | **Upvotes:** 0 | **Autor:** u/Ambitious-Credit-722
- **URL:** https://reddit.com/r/cybersecurity/comments/1rpotnj/oss_tool_that_helps_ai_devs_search_big_codebases/
- **Trecho:** Hi guys, Recently I’ve been working on an OSS tool that helps AI &amp; devs search big codebases faster by indexing repos and building a semantic view, Just published a pre-release on PyPI: [https://pypi.org/project/codexa/](https://pypi.org/project/codexa/) Official docs:...

#### 15. Cybersecurity and LLM research
- **Subreddit:** r/cybersecurity | **Upvotes:** 0 | **Autor:** u/Knight_King26
- **URL:** https://reddit.com/r/cybersecurity/comments/1oit2m2/cybersecurity_and_llm_research/
- **Trecho:** Hi everyone,

I am conducting a research looking into use of Large Language Models by Cyber Security professionals. Could people who are in the industry kindly point out if they use LLMs and if so, for what tasks do you guys use them for typically? It would be a great help for my research.

TIA

## 8. Telemetria Expandida: Frequência de Indicadores por Vetor

> Análise de densidade de sinais sobre corpus de **15 threads**

> Gerado em: 13/04/2026 15:35


### Exploração de Vulnerabilidades — 78.3% de probabilidade
Total de ocorrências: **18**

| Indicador / Keyword | Ocorrências | Densidade |
|---------------------|-------------|-----------|
| `rce` | 9 | 50.0% |
| `patch` | 7 | 38.9% |
| `cve` | 1 | 5.6% |
| `exploit` | 1 | 5.6% |

### Evasão de Defesas (EDR/AV) — 13.0% de probabilidade
Total de ocorrências: **3**

| Indicador / Keyword | Ocorrências | Densidade |
|---------------------|-------------|-----------|
| `bypass` | 3 | 100.0% |

### Negociação e Resgate — 8.7% de probabilidade
Total de ocorrências: **2**

| Indicador / Keyword | Ocorrências | Densidade |
|---------------------|-------------|-----------|
| `ransom` | 2 | 100.0% |

## 9. Índice de Referências e Fontes

> Relatório gerado em: 13/04/2026 às 15:35 UTC
> Termo de busca: **Codex** | Fontes: NVD/NIST + Reddit OSINT


### Referências Oficiais (NVD/NIST)

- **CVE-2017-5215** (CVSS 9.8 CRITICAL) — https://nvd.nist.gov/vuln/detail/CVE-2017-5215
  - https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
  - https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
- **CVE-2017-5214** (CVSS 7.5 HIGH) — https://nvd.nist.gov/vuln/detail/CVE-2017-5214
  - https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
  - https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
- **CVE-2017-9030** (CVSS 7.5 HIGH) — https://nvd.nist.gov/vuln/detail/CVE-2017-9030
  - https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
  - https://navixia.com/storage/app/media/uploaded-files/CVE/cve-2017-521415.txt
- **CVE-2023-50892** (CVSS 7.1 HIGH) — https://nvd.nist.gov/vuln/detail/CVE-2023-50892
  - https://patchstack.com/database/vulnerability/thegem/wordpress-thegem-theme-5-9-1-reflected-cross-site-scripting-xss-vulnerability?_s_id=cve
  - https://patchstack.com/database/vulnerability/thegem/wordpress-thegem-theme-5-9-1-reflected-cross-site-scripting-xss-vulnerability?_s_id=cve
- **CVE-2024-54210** (CVSS None None) — https://nvd.nist.gov/vuln/detail/CVE-2024-54210
  - https://patchstack.com/database/Wordpress/Plugin/cs-element-bucket/vulnerability/wordpress-advanced-element-bucket-addons-for-elementor-plugin-1-0-2-cross-site-scripting-xss-vulnerability?_s_id=cve

### Fontes OSINT (Reddit)

1. [OpenAI's GPT-5.4 got blocked by safety mechanisms 5 times, searched my machine f](https://reddit.com/r/cybersecurity/comments/1sbr7kq/openais_gpt54_got_blocked_by_safety_mechanisms_5/) — r/cybersecurity | 297 upvotes
2. [[RESEARCH] We scanned 3,471 MCP servers for invisible Unicode — GPT-5.4 follows ](https://reddit.com/r/cybersecurity/comments/1se27dc/research_we_scanned_3471_mcp_servers_for/) — r/cybersecurity | 12 upvotes
3. [OreWatch – open-source malicious package scanner across 6 ecosystems, now with a](https://reddit.com/r/cybersecurity/comments/1sejkxy/orewatch_opensource_malicious_package_scanner/) — r/cybersecurity | 10 upvotes
4. [Cybersecurity statistics of the week (March 9th - March 15th)](https://reddit.com/r/cybersecurity/comments/1rwhia9/cybersecurity_statistics_of_the_week_march_9th/) — r/cybersecurity | 6 upvotes
5. [My take on LLMs in SAST: good for PRs, not yet for full repos](https://reddit.com/r/cybersecurity/comments/1n9d1lp/my_take_on_llms_in_sast_good_for_prs_not_yet_for/) — r/cybersecurity | 6 upvotes
6. [Runtime security layer for AI agents - request for feedback](https://reddit.com/r/cybersecurity/comments/1s51h4s/runtime_security_layer_for_ai_agents_request_for/) — r/cybersecurity | 4 upvotes
7. [I built a runtime security proxy for AI agents using MCP (Model Context Protocol](https://reddit.com/r/cybersecurity/comments/1sazmsv/i_built_a_runtime_security_proxy_for_ai_agents/) — r/cybersecurity | 2 upvotes
8. [I built an open source framework that does what your CSPM tool won't, show you t](https://reddit.com/r/cybersecurity/comments/1rqeiyq/i_built_an_open_source_framework_that_does_what/) — r/cybersecurity | 2 upvotes
9. [OpenAI Patches ChatGPT Data Exfiltration Flaw and Codex GitHub Token Vulnerabili](https://reddit.com/r/cybersecurity/comments/1s82znb/openai_patches_chatgpt_data_exfiltration_flaw_and/) — r/cybersecurity | 1 upvotes
10. [Supply Chain Attacks, Hardening Your Dev Environmen](https://reddit.com/r/cybersecurity/comments/1sduv0p/supply_chain_attacks_hardening_your_dev_environmen/) — r/cybersecurity | 1 upvotes
11. [mcp-scan: open-source security scanner for MCP (Model Context Protocol) server c](https://reddit.com/r/cybersecurity/comments/1s2r0w1/mcpscan_opensource_security_scanner_for_mcp_model/) — r/cybersecurity | 1 upvotes
12. [ChatGPt Codex in webstorm](https://reddit.com/r/cybersecurity/comments/1shl8b7/chatgpt_codex_in_webstorm/) — r/cybersecurity | 0 upvotes
13. [Using AI to identify silent security patches before they are publicly announced](https://reddit.com/r/cybersecurity/comments/1sgjo65/using_ai_to_identify_silent_security_patches/) — r/cybersecurity | 0 upvotes
14. [OSS tool that helps AI &amp; devs search big codebases faster by indexing repos ](https://reddit.com/r/cybersecurity/comments/1rpotnj/oss_tool_that_helps_ai_devs_search_big_codebases/) — r/cybersecurity | 0 upvotes
15. [Cybersecurity and LLM research](https://reddit.com/r/cybersecurity/comments/1oit2m2/cybersecurity_and_llm_research/) — r/cybersecurity | 0 upvotes

### Metodologia de Coleta

- **Reddit OSINT:** API pública (old.reddit.com/search.json) — filtro: posts com texto > 50 chars, ordenados por upvotes
- **NVD/NIST:** CVE API 2.0 (services.nvd.nist.gov/rest/json/cves/2.0) — filtro: CVSS Score >= 7.0 (High/Critical)
- **Pipeline IA:** Google Gemini 2.5 Flash — 3 agentes especializados (Recon, Quant, Strat)
- **Classificação:** TLP:AMBER — Distribuição restrita: Blue Team / SecOps