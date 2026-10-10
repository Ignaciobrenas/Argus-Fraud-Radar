<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../assets/logo_white.png">
    <source media="(prefers-color-scheme: light)" srcset="../assets/logo_black.png">
    <img alt="ARGUS Fraud Radar" src="../assets/logo_black.png" width="420">
  </picture>
</p>

# Documentation Index — ARGUS Fraud Radar
**Datacycle · Unit 1 · Case 2: Retail Banking Real-Time Fraud Detection**

Welcome to the technical and academic documentation for **ARGUS Fraud Radar**. This repository implements an end-to-end data and machine learning streaming architecture for real-time banking fraud detection within the academic context of **STUCOM Pelai** and the European **UNITA Erasmus+ BIP** consortium.

---

## 📚 English Documentation Directory

| Document | Description |
|---|---|
| [1. Technical Architecture](architecture.md) | Medallion architecture (Bronze, Silver, Gold), streaming vs batch engines, and full technology stack. |
| [2. Data Classification](data_classification.md) | Taxonomy of the 7 datasets, structured vs semi-structured data, and PII / GDPR compliance. |
| [3. DIKW Pyramid Model](dikw.md) | The DIKW framework (Data, Information, Knowledge, Wisdom) applied to a live banking transaction. |
| [4. Data Lifecycle](lifecycle.md) | The 7 stages of data lifecycle from synthetic generation to long-term ZSTD cold storage. |
| [5. Data Lineage & Traceability](lineage.md) | End-to-end lineage flow, Mermaid diagrams, and column-level traceability matrix. |
| [6. Metadata Strategy & Governance](metadata.md) | The 4 mandatory governance metadata tags and semantic schema evolution policy. |
| [7. Fraud Patterns & Attack Vectors](fraud_patterns.md) | Detailed specifications and detection vectors for the 8 injected fraud patterns. |
| [8. Comparative Scenarios & KPI](scenarios_and_kpi.md) | Comparison of Scenario A (batch), B (stream rules), and C (stream ML), plus primary KPI calculation. |
| [9. Data Generation Prompt](data_generation_prompt.md) | Exact prompt engineering evidence used with the LLM to design the data architecture. |
| [10. Academic Context & UNITA BIP](unita_bip.md) | European UNITA Erasmus+ BIP initiative, STUCOM Pelai DAW 2, and MOPT2 AI module. |

---

## 🌐 Documentación en Español
La documentación académica completa también está disponible en español en la carpeta [`docs/es/`](../es/index.md).
