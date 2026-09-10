#!/usr/bin/env python3
"""
Gera plugins Claude Code a partir das skills em skills/.

Uso:  python3 scripts/build-skill-plugins.py [--check]

- Lê skills/<categoria>/<skill>/SKILL.md
- Agrupa por tema (GROUPS)
- Copia para plugins/skills/<grupo>/skills/<name>/
- Escreve .claude-plugin/plugin.json de cada grupo
- Atualiza .claude-plugin/marketplace.json preservando entradas upstream

Reexecute após dar sync com o upstream.
"""
import json, os, re, shutil, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "skills")
OUT = os.path.join(ROOT, "plugins", "skills")
MARKET = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
VERSION = "1.0.0"

# Já entregues por outros plugins do marketplace -> não duplicar
EXCLUDE = {
    "gcloud", "google-cloud-recipe-auth", "google-cloud-recipe-onboarding",
    "finding-google-skills", "retrieving-developer-knowledge",
    "google-cloud-storage-basics", "google-cloud-storage-bucket-architect",
    "google-cloud-storage-fuse",
}

# (slug, título, descrição, [regex]) — primeira regra que casar vence
GROUPS = [
    ("google-gke", "Google Kubernetes Engine",
     "GKE: criação de cluster, autoscaling, networking, segurança, upgrades, custo, observabilidade e troubleshooting de workloads e de GPU/TPU.",
     [r"^gke-"]),
    ("google-ai-platform", "Google AI & Agent Platform",
     "Vertex/Agent Platform e Gemini: deploy e tuning de modelos, RAG engine, prompt management, avaliação, inferência, APIs Gemini e SDK Genkit.",
     [r"^agent-platform-", r"^gemini-", r"^genkit-", r"^developing-genkit-", r"^google-agents-cli-onboarding$"]),
    ("google-data", "Google Cloud Data",
     "BigQuery, AlloyDB, Bigtable, Spanner, Cloud SQL, Data Lineage e Managed Airflow (Composer): modelagem, consulta, ingestão e orquestração.",
     [r"^bigquery-", r"^alloydb-", r"^bigtable-", r"^spanner-", r"^cloud-sql-",
      r"^cloud-databases-onboarding$", r"^datalineage-", r"^managed-airflow-"]),
    ("google-observability", "Google Cloud Observability",
     "Cloud Logging, Cloud Monitoring, PromQL, SLO/alerting e observabilidade de rede no Google Cloud.",
     [r"^cloud-logging-", r"^cloud-monitoring-", r"^google-cloud-slo-",
      r"^google-cloud-networking-observability$"]),
    ("google-security-iam", "Google Cloud Security & IAM",
     "IAM (políticas, simulator, PAM, troubleshooting), Security Command Center e avaliação de cobertura de detecção.",
     [r"^iam-helper-", r"^google-cloud-scc-query$", r"^detection-engineering-"]),
    ("google-storage", "Google Cloud Filestore",
     "Filestore: auditoria, autoscaling e navegação NFS.",
     [r"^google-cloud-filestore-"]),
    ("google-architecture", "Google Cloud Architecture",
     "Well-Architected Framework, arquiteturas de solução de referência (agentic AI, RAG, serverless, lakehouse) e Application Design Center.",
     [r"^google-cloud-solution-", r"^google-cloud-waf-",
      r"^application-design-center-", r"^google-cloud-recipe-foundation-builder$"]),
    ("google-cloud-core", "Google Cloud Core",
     "Cloud Run, Cloud Build, Firebase, Workload Manager, frontend global e device platform — o básico de compute e deploy no Google Cloud.",
     [r"^cloud-run-", r"^cloud-build-", r"^firebase-", r"^workload-manager-",
      r"^developer-device-platform-", r"^google-cloud-global-frontend-"]),
    ("google-ads", "Google Ads & Mobile Ads",
     "Google Ads API, Data Manager API, Google Mobile Ads SDK (banner, interstitial, rewarded) e IMA SDK.",
     [r"^google-ads-api-", r"^data-manager-api-", r"^google-mobile-ads-", r"^ima-"]),
    ("google-analytics", "Google Analytics",
     "Google Analytics Admin API e Data API: configuração de propriedades e extração de relatórios.",
     [r"^google-analytics-"]),
    ("google-identity", "Google Identity",
     "OAuth 2.0 e identidade Google, incluindo adoção de DPoP (RFC 9449) para sender-constrained refresh tokens.",
     [r"^dpop-"]),
]

def read_fm(path):
    txt = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
    if not m:
        raise SystemExit(f"frontmatter ausente: {path}")
    return yaml.safe_load(m.group(1))

def discover():
    found = {}
    for cat in sorted(os.listdir(SRC)):
        catdir = os.path.join(SRC, cat)
        if not os.path.isdir(catdir):
            continue
        for d in sorted(os.listdir(catdir)):
            sd = os.path.join(catdir, d)
            if not os.path.isfile(os.path.join(sd, "SKILL.md")):
                continue
            fm = read_fm(os.path.join(sd, "SKILL.md"))
            found[fm["name"]] = dict(dir=sd, folder=d, fm=fm)
    return found

def assign(name):
    for slug, _t, _d, pats in GROUPS:
        if any(re.search(p, name) for p in pats):
            return slug
    return None

def validate(name, info):
    errs = []
    if info["folder"] != name:
        errs.append(f"{name}: pasta '{info['folder']}' != name")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        errs.append(f"{name}: slug inválido")
    if any(w in name for w in ("claude", "anthropic")):
        errs.append(f"{name}: palavra reservada no name")
    desc = " ".join((info["fm"].get("description") or "").split())
    if not desc:
        errs.append(f"{name}: description vazia")
    if len(desc) > 1024:
        errs.append(f"{name}: description {len(desc)} chars (>1024)")
    if "<" in desc and ">" in desc:
        errs.append(f"{name}: description pode conter tag XML")
    return errs

def main():
    check = "--check" in sys.argv
    found = discover()
    errs, unassigned, buckets = [], [], {}
    for name, info in sorted(found.items()):
        errs += validate(name, info)
        if name in EXCLUDE:
            continue
        g = assign(name)
        if g is None:
            unassigned.append(name)
        else:
            buckets.setdefault(g, []).append((name, info))
    if unassigned:
        errs.append("sem grupo: " + ", ".join(unassigned))
    if errs:
        print("ERROS:")
        for e in errs:
            print("  -", e)
        return 1
    if check:
        for slug, t, _d, _p in GROUPS:
            print(f"{slug:24} {len(buckets.get(slug, [])):3}  {t}")
        print(f"{'TOTAL':24} {sum(len(v) for v in buckets.values()):3}  "
              f"({len(EXCLUDE)} excluídas por duplicidade)")
        return 0

    # limpa só os diretórios de grupo (preserva README.md deste diretório)
    for slug, *_ in GROUPS:
        gdir = os.path.join(OUT, slug)
        if os.path.isdir(gdir):
            shutil.rmtree(gdir)
    os.makedirs(OUT, exist_ok=True)
    entries = []
    for slug, title, gdesc, _p in GROUPS:
        items = buckets.get(slug, [])
        if not items:
            continue
        pdir = os.path.join(OUT, slug)
        os.makedirs(os.path.join(pdir, ".claude-plugin"), exist_ok=True)
        for name, info in items:
            shutil.copytree(info["dir"], os.path.join(pdir, "skills", name))
        desc = f"{gdesc} ({len(items)} skills)"
        json.dump({
            "name": slug, "displayName": title, "version": VERSION,
            "description": desc,
            "author": {"name": "Google LLC"},
            "homepage": "https://github.com/solon07/google-skills",
            "keywords": ["google", "google-cloud", slug.replace("google-", "")],
        }, open(os.path.join(pdir, ".claude-plugin", "plugin.json"), "w"),
            indent=2, ensure_ascii=False)
        entries.append({
            "name": slug,
            "source": f"./plugins/skills/{slug}",
            "description": desc,
        })

    mk = json.load(open(MARKET, encoding="utf-8"))
    keep = [p for p in mk["plugins"] if p["name"] not in {e["name"] for e in entries}]
    mk["plugins"] = keep + entries
    json.dump(mk, open(MARKET, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(MARKET, "a", encoding="utf-8").write("\n")

    print(f"{sum(len(v) for v in buckets.values())} skills em {len(entries)} plugins.")
    for e in entries:
        print(f"  {e['name']:24} {len(buckets[e['name']]):3}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
