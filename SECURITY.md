# ================================================================================
# SECURITY BEST PRACTICES - AI Learning System
# ================================================================================

## 🔒 SIGURNOSNA CHECKLISTA

### 1. GitHub Token
- [ ] Token ima samo `repo` i `workflow` scope
- [ ] Token se rotira svakih 90 dana
- [ ] Token NIJE u kodu (samo u secrets)
- [ ] Koristi fine-grained token

### 2. GitHub Actions
```yaml
# MINIMUM REQUIRED PERMISSIONS
permissions:
  contents: read        # Čitanje koda
  issues: read         # Čitanje issues
  pull-requests: read  # Čitanje PRs
  actions: read        # Čitanje workflow statusa
  # NE DODAJ: contents: write, issues: write
```

### 3. Secrets Management
- [ ] GITHUB_TOKEN u repo secrets
- [ ] DISCORD_WEBHOOK u repo secrets  
- [ ] Nema secrets u `.env` fajlovima
- [ ] `.env` je u `.gitignore`

### 4. Network Security
- [ ] Samo outbound API pozivi
- [ ] Nema expose-ovanih credentials
- [ ] Koristi HTTPS svuda

---

## 🚨 INCIDENT RESPONSE PLAN

### Ako je token kompromitovan:

```bash
# 1. Odmah rotiraj token
# https://github.com/settings/tokens

# 2. Revoke stari token
# Settings → Developer settings → Personal access tokens → Revoke

# 3. Proveri audit log
# Settings → Audit log

# 4. Kreiraj novi token i ažuriraj secrets
```

### Ako CI fails:

```
1. GitHub šalje notification
2. Workflow kreira issue sa label "ci-failed"
3. Developer dobija notification
4. Fix-uje problem
5. Push-uje fix
```

---

## 📋 SECURITY AUDIT CHECKLIST

### Mesečno:
- [ ] Proveri audit log
- [ ] Rotiraj token
- [ ] Proveri secrets
- [ ] Review workflow permissions

### Kvartalno:
- [ ] Security audit celokupnog sistema
- [ ] Proveri da nema exposed credentials
- [ ] Update dependencies
- [ ] Review access logs
