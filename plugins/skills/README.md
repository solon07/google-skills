# Skill plugins

Plugins gerados a partir de `skills/`, para instalar via marketplace no Claude Code / Cowork
em vez de subir cada skill manualmente como `.zip` no claude.ai.

## Instalar

```bash
# 1. registrar o marketplace (uma vez)
/plugin marketplace add solon07/google-skills

# 2. instalar só os grupos que interessam
/plugin install google-gke@google-plugins
/plugin install google-observability@google-plugins
```

Cada plugin é independente: habilite/desabilite por grupo em `/plugin` para controlar
quanto contexto as descrições de skill ocupam por sessão.

| Plugin | Skills | Escopo |
| --- | --- | --- |
| `google-gke` | 32 | Cluster, autoscaling, networking, segurança, upgrades, custo, troubleshooting GPU/TPU |
| `google-ai-platform` | 22 | Agent Platform/Vertex, Gemini APIs, Genkit |
| `google-architecture` | 19 | Well-Architected Framework, arquiteturas de referência, Application Design Center |
| `google-ads` | 14 | Google Ads API, Data Manager API, Mobile Ads, IMA SDK |
| `google-data` | 13 | BigQuery, AlloyDB, Bigtable, Spanner, Cloud SQL, Data Lineage, Managed Airflow |
| `google-observability` | 9 | Cloud Logging, Cloud Monitoring, PromQL, SLO/alerting |
| `google-security-iam` | 6 | IAM, Security Command Center, detection engineering |
| `google-cloud-core` | 6 | Cloud Run, Cloud Build, Firebase, Workload Manager |
| `google-storage` | 3 | Filestore |
| `google-analytics` | 2 | Admin API, Data API |
| `google-identity` | 1 | OAuth 2.0 DPoP |

Total: 127 skills.

## Skills não incluídas

8 skills de `skills/` ficam de fora por já serem entregues por outros plugins deste
marketplace (evita duplicidade no roteamento):

- `google-cloud-developer`: `gcloud`, `google-cloud-recipe-auth`,
  `google-cloud-recipe-onboarding`, `finding-google-skills`, `retrieving-developer-knowledge`
- `google-cloud-storage`: `google-cloud-storage-basics`,
  `google-cloud-storage-bucket-architect`, `google-cloud-storage-fuse`

Para incluí-las, remova o nome de `EXCLUDE` em `scripts/build-skill-plugins.py`.

## Regerar

Este diretório é **gerado**. Não edite à mão — edite `skills/` e rode:

```bash
python3 scripts/build-skill-plugins.py --check   # valida e mostra o agrupamento
python3 scripts/build-skill-plugins.py           # regenera + atualiza marketplace.json
```

O script valida frontmatter (`name` = nome da pasta, slug válido, `description` não vazia
e ≤ 1024 chars, sem palavras reservadas) e falha antes de escrever qualquer coisa.
Rode depois de todo sync com o upstream.
