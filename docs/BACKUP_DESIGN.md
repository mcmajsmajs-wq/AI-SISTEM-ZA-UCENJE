# AI Learning System - Backup Design Document

**Version:** 1.0  
**Date:** 2026-04-25  
**Status:** DESIGN PHASE

---

## 1. Overview

### 1.1 Cilj

Kreirati potpuno automatski backup sistem koji osigurava:
- Business continuity u slučaju katastrofe
- Brzi restore bez gubitka podataka
- Minimalan downtime
- Samoodrživost bez ljudske intervencije

### 1.2 RTO/RPO Definicije

| Metric | Target | Objašnjenje |
|--------|-------|------------|
| **RTO** (Recovery Time Objective) | < 1 sat | vrijeme do potpunog recovery-a |
| **RPO** (Recovery Point Objective) | < 24h | maksimalni gubitak podataka |

---

## 2. Backup Tipovi

### 2.1 Full Backup

```
Opis: Kompletna kopija svih podataka
Kada: Nedjelja u 02:00
Veličina: ~300MB (kompresovano)
Trajanje: ~5 minuta
Storage: 7 dana rotacija
```

### 2.2 Incremental Backup

```
Opis: Samo promene od zadnjeg backup-a
Kada: Ponedjeljak-Subota u 02:00
Veličina: ~10-50MB (varira)
Trajanje: ~1-2 minute
Storage: 6 dana rotacija
依赖于: Zadnji full ili incremental
```

### 2.3 Differential Backup (Opcija)

```
Opis: Promjene od zadnjeg FULL backup-a
Kada: Daily
Veličina: ~50-100MB
Koristi se za: Brzi restore bez iteracija
```

---

## 3. Šta Backup-ovati

### 3.1 Kritični Podaci (OBVEZNO)

| Komponenta | Tip | Metoda | Prioritet |
|-----------|-----|-------|-----------|
| **PostgreSQL** | Database | `pg_dump` | KRITIČNO |
| **MinIO/S3** | Files | `mc mirror` | KRITIČNO |
| **Config** | Files | `tar.gz` | VISOK |

### 3.2 Konfiguracija

| Fajl | Lokacija | Zašto |
|-------|---------|-------|
| `.env` | `docker/.env` | Sve config varijable |
| `nginx.conf` | `docker/nginx/` | Reverse proxy |
| `prometheus.yml` | `docker/prometheus/` | Metrics config |

### 3.3 Ne Backup-ovati

| Šta | Zašto |
|------|-------|
| Redis podaci | Ephemeral, rebuild on restart |
| Cache | Regeneriše se |
| Logs | Rotate, ne kritično |
| node_modules | Reinstall |
| Git | Ima remote |

---

## 4. Storage Strategija

### 4.1 Primarni Storage

```
Local: /backups (na serveru)
├── full/
│   └── ai-learning-full-YYYY-MM-DD.tar.gz
├── incremental/
│   └── ai-learning-incr-YYYY-MM-DD.tar.gz
└── config/
    └── ai-learning-config-latest.tar.gz
```

### 4.2 Disaster Recovery Storage

```
Remote: MinIO bucket "backups" ili ekstern disk
├── weekly/monthly arhive
└── Off-site copy
```

### 4.3 Rotacija

```
FULL BACKUP:
├── daily/        (7 dana) - full-YYYY-MM-DD.tar.gz
├── weekly/      (4 nedjelje) - full-WN-DD.tar.gz  
└── monthly/     (12 mjeseci) - full-YYYY-MM.tar.gz

INCREMENTAL:
├── daily/       (6 dana) - inc-YYYY-MM-DD.tar.gz
└── (briše se nakon sljedećeg full)
```

---

## 5. Backup Procedure

### 5.1 Full Backup Procedura

```
STEP 1: Lock/konsistentnost
  └── docker pause app (opcija) ili FLUSH TABLES

STEP 2: Database dump  
  └── pg_dump -Fc ai_learning_db > full-db-YYYYMMDD.dump

STEP 3: MinIO mirror
  └── mc mirror local/backup s3/bucket/full/

STEP 4: Config archive
  └── tar czf config-YYYYMMDD.tar.gz docker/.env docker/nginx/

STEP 5: Metadata
  └── echo "{timestamp, type: full, size: N}" > backup-meta.json

STEP 6: Verify
  └── ls -la backup-*.tar.gz
  └── md5sum > CHECKSUM
```

### 5.2 Incremental Backup Procedura

```
STEP 1: Database since last
  └── pg_dump --增量=since-last-full ai_learning_db > inc-db-YYYYMMDD.sql

STEP 2: MinIO changes since last
  └── mc diff local/backup s3/bucket/incremental/

STEP 3: Store
  └── tar czf inc-YYYYMMDD.tar.gz

STEP 4: Update last backup timestamp
  └── echo timestamp > .last_backup
```

---

## 6. Restore Procedure

### 6.1 Full Restore

```
OPREZ: Stop_services
  └── docker-compose stop app worker

STEP 1: Database
  └── dropdb ai_learning_db
  └── createdb ai_learning_db
  └── pg_restore -d ai_learning_db full-db-YYYYMMDD.dump

STEP 2: MinIO
  └── mc rm --recursive s3/bucket/data/
  └── mc mirror s3/bucket/full/ local/restore/

STEP 3: Config
  └── tar xzf config-backup.tar.gz -C docker/

STEP 4: Verify
  └── curl http://localhost:8010/health

STEP 5: Start_services
  └── docker-compose start app worker
```

### 6.2 Point-in-Time Restore (PITR)

```
Koristi se za: Recovery do određene tačke
Zahtijeva: Full backup + svi incrementals do te tačke

STEP 1: Restore full
  └── pg_restore full-db-YYYYMMDD.dump

STEP 2: Apply incrementals in order
  └── psql < inc-db-YYYYMMDD-1.sql
  └── psql < inc-db-YYYYMMDD-2.sql
```

---

## 7. Monitoring & Alerts

### 7.1 Status Check

| Event | Action |
|-------|--------|
| Backup uspješan | OK log |
| Backup fail | Alert na webhook |
| Size 0 | Alert |
| Storage > 90% | Alert |

### 7.2 Webhook Alerts

```bash
# Discord/Slack format
{
  "title": "🚨 Backup Failed",
  "description": "Full backup nije uspio",
  "timestamp": "2026-04-25T02:00:00Z"
}
```

---

## 8. Cron Schedule

### 8.1 Default Schedule

```bash
# /etc/cron.d/ai-learning-backup

# Full backup - Nedjelja 02:00
0 2 * * 0 root /home/dju/scripts/backup.sh --type=full

# Incremental backup - Ponedjeljak-Subota 02:00
0 2 * * 1-6 root /home/dju/scripts/backup.sh --type=incremental

# Monthly archive - 1. u mjesecu 03:00
0 3 1 * * root /home/dju/scripts/backup.sh --type=archive
```

### 8.2 Retention Policy

```
Dnevni: 7 dana
Nedjeljni: 4 nedjelje
Mjesečni: 12 mjeseci
```

---

## 9. Verification Procedure

### 9.1 Pre-restore Test (mjesečno)

```
1. Kreiraj test database
2. Restore backup u test DB
3. Verify schema integrity
4. Verify row counts
5. Verify data integrity (sample queries)
6. Drop test database
7. Report rezultat
```

### 9.2 Disaster Recovery Test (kvartalno)

```
1. Stop services
2. Restore na test server
3. Verify all services start
4. Verify API endpoints
5. Verify data integrity
6. Full report
```

---

## 10. Error Handling

### 10.1 Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | OK |
| 1 | Backup fail | Alert |
| 2 | Verify fail | Alert |
| 3 | Storage full | Alert |

### 10.2 Retry Policy

```
Retry: 3 puta sa 5 min pauzom
After 3 failures: Alert + skip
```

---

## 11. Implementation Notes

### 11.1 Sve skripte idu u:
```
/home/dju/scripts/
├── backup.sh           # Main backup script
├── restore.sh         # Restore script  
├── backup-cron.sh     # Cron wrapper
└── .env             # Config (iz source control excl.)
```

### 11.2 Secrets

```bash
# Ne commituj!
BACKUP_ENCRYPTION_KEY=
REMOTE_STORAGE_KEY=
WEBHOOK_URL=
```

---

## 12. Verification Checklist

- [ ] pg_dump radi
- [ ] MinIO mirror radi
- [ ] Restore radi
- [ ] Cron radi
- [ ] Alerti šalju
- [ ] Retention radi
- [ ] Disk space dovoljan
- [ ] Testiran restore (mjesečno)

---

**Next Phase:** Implementacija skripti