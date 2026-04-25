#!/usr/bin/env bash
# ================================================================================
# deploy.sh — Skripta za deployment AI Learning System-a
# ================================================================================
# Upotreba:
#   ./scripts/deploy.sh --env local
#   ./scripts/deploy.sh --env staging --tag latest
#   ./scripts/deploy.sh --env production --tag v1.2.3
#
# Potrebne environment varijable za staging/production:
#   STAGING_SSH_HOST, STAGING_SSH_USER, STAGING_SSH_KEY, STAGING_SSH_PORT,
#   STAGING_APP_DIR
#   PRODUCTION_SSH_HOST, PRODUCTION_SSH_USER, PRODUCTION_SSH_KEY,
#   PRODUCTION_SSH_PORT, PRODUCTION_APP_DIR
#
# Opcioni secrets (za Docker Hub pull na serveru):
#   DOCKER_HUB_USERNAME, DOCKER_HUB_TOKEN
# ================================================================================

set -euo pipefail

# ── Boje za output ───────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Helper funkcije za logging ────────────────────────────────────────────────
log_info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_step()    { echo -e "\n${CYAN}${BOLD}══ $* ══${NC}"; }
log_banner()  {
  echo -e "${BOLD}"
  echo "╔══════════════════════════════════════════════════════╗"
  echo "║         AI Learning System — Deploy Script           ║"
  echo "╚══════════════════════════════════════════════════════╝"
  echo -e "${NC}"
}

# ── Globalne varijable ────────────────────────────────────────────────────────
ENV=""
TAG="latest"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

# ── Parsiranje argumenata ─────────────────────────────────────────────────────
usage() {
  cat << EOF
${BOLD}Upotreba:${NC}
  $0 --env ENV [--tag TAG] [--help]

${BOLD}Argumenti:${NC}
  --env ENV    Okruženje: local | staging | production  (obavezno)
  --tag TAG    Docker image tag ili git tag (default: latest)
  --help       Prikaži ovu poruku

${BOLD}Primjeri:${NC}
  $0 --env local
  $0 --env staging --tag latest
  $0 --env production --tag v1.2.3

${BOLD}Potrebne env varijable za staging:${NC}
  STAGING_SSH_HOST, STAGING_SSH_USER, STAGING_SSH_KEY
  STAGING_SSH_PORT (default: 22), STAGING_APP_DIR

${BOLD}Potrebne env varijable za production:${NC}
  PRODUCTION_SSH_HOST, PRODUCTION_SSH_USER, PRODUCTION_SSH_KEY
  PRODUCTION_SSH_PORT (default: 22), PRODUCTION_APP_DIR
EOF
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      ENV="$2"
      shift 2
      ;;
    --tag)
      TAG="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      log_error "Nepoznati argument: $1"
      usage
      exit 1
      ;;
  esac
done

# ── Validacija argumenata ─────────────────────────────────────────────────────
validate_args() {
  if [[ -z "$ENV" ]]; then
    log_error "--env je obavezan argument"
    usage
    exit 1
  fi

  if [[ "$ENV" != "local" && "$ENV" != "staging" && "$ENV" != "production" ]]; then
    log_error "Nevalidno okruženje: '$ENV'. Moguće vrijednosti: local, staging, production"
    exit 1
  fi

  # Validacija tag formata za produkciju
  if [[ "$ENV" == "production" && "$TAG" != "latest" ]]; then
    if ! echo "$TAG" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+'; then
      log_warn "Tag '$TAG' ne prati semantic versioning (vX.Y.Z format)"
      read -r -p "Nastaviti? [y/N] " confirm
      [[ "$confirm" =~ ^[Yy]$ ]] || { log_info "Deploy otkazan."; exit 0; }
    fi
  fi
}

# ── Pre-deploy provjere ───────────────────────────────────────────────────────
pre_deploy_check_local() {
  log_step "Pre-deploy provjera (local)"

  # Docker daemon mora biti pokrenut
  if ! docker info > /dev/null 2>&1; then
    log_error "Docker nije pokrenut! Pokrenite Docker daemon."
    exit 1
  fi
  log_success "Docker je dostupan"

  # .env mora postojati
  if [[ ! -f "$DOCKER_DIR/.env" ]]; then
    log_warn "$DOCKER_DIR/.env ne postoji — kopiram iz .env.example"
    if [[ -f "$DOCKER_DIR/.env.example" ]]; then
      cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"
      log_warn "Uredite $DOCKER_DIR/.env sa pravim vrijednostima!"
    else
      log_error ".env.example nije pronađen. Kreiran prazan .env"
      touch "$DOCKER_DIR/.env"
    fi
  fi
  log_success ".env fajl postoji"

  # docker-compose.yml mora postojati
  if [[ ! -f "$DOCKER_DIR/docker-compose.yml" ]]; then
    log_error "$DOCKER_DIR/docker-compose.yml nije pronađen!"
    exit 1
  fi
  log_success "docker-compose.yml postoji"
}

pre_deploy_check_remote() {
  local env_upper="${ENV^^}"
  log_step "Pre-deploy provjera ($ENV)"

  # Provjera potrebnih varijabli
  local required_vars=(
    "${env_upper}_SSH_HOST"
    "${env_upper}_SSH_USER"
    "${env_upper}_SSH_KEY"
    "${env_upper}_APP_DIR"
  )

  local missing=()
  for var in "${required_vars[@]}"; do
    if [[ -z "${!var:-}" ]]; then
      missing+=("$var")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_error "Nedostaju environment varijable:"
    for var in "${missing[@]}"; do
      log_error "  - $var"
    done
    log_error "Postavite ih u shell okruženju ili exportujte iz .env fajla"
    exit 1
  fi
  log_success "Sve potrebne env varijable su dostupne"

  # Postavljanje varijabli za ovaj deploy
  SSH_HOST="${!${env_upper}_SSH_HOST}"
  SSH_USER="${!${env_upper}_SSH_USER}"
  SSH_KEY="${!${env_upper}_SSH_KEY}"
  SSH_PORT="${!${env_upper}_SSH_PORT:-22}"
  APP_DIR="${!${env_upper}_APP_DIR}"

  # Provjera SSH ključa
  if [[ ! -f "$SSH_KEY" ]]; then
    log_error "SSH ključ nije pronađen: $SSH_KEY"
    exit 1
  fi
  # Ispravne permisije za SSH ključ
  chmod 600 "$SSH_KEY"
  log_success "SSH ključ: $SSH_KEY"

  # Test SSH konekcije
  log_info "Testiranje SSH konekcije na $SSH_USER@$SSH_HOST:$SSH_PORT..."
  if ! ssh -i "$SSH_KEY" \
       -p "$SSH_PORT" \
       -o ConnectTimeout=10 \
       -o StrictHostKeyChecking=accept-new \
       -o BatchMode=yes \
       "$SSH_USER@$SSH_HOST" "echo 'SSH OK'" > /dev/null 2>&1; then
    log_error "SSH konekcija NEUSPJEŠNA! Provjeri host, user, ključ i port."
    exit 1
  fi
  log_success "SSH konekcija uspješna: $SSH_USER@$SSH_HOST:$SSH_PORT"
}

# ── Health check ──────────────────────────────────────────────────────────────
health_check_local() {
  log_step "Health check (local)"
  local max_retries=10
  local retry_interval=5
  local url="http://localhost:8000/health"

  log_info "Čekanje na pokretanje servisa..."
  sleep 10

  for i in $(seq 1 $max_retries); do
    log_info "Pokušaj $i/$max_retries: $url"
    if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
      local resp
      resp=$(curl -s "$url")
      log_success "Health check prošao! Odgovor: $resp"
      return 0
    fi
    sleep $retry_interval
  done

  log_error "Health check NEUSPJEŠAN nakon $max_retries pokušaja!"
  log_info "Logovi servisa:"
  cd "$DOCKER_DIR" && docker compose logs --tail=30 app || true
  return 1
}

health_check_remote() {
  log_step "Health check ($ENV — $SSH_HOST)"
  local max_retries=8
  local retry_interval=10

  log_info "Čekanje na inicijalizaciju servisa (30s)..."
  sleep 30

  for i in $(seq 1 $max_retries); do
    log_info "Pokušaj $i/$max_retries..."
    if ssh -i "$SSH_KEY" \
         -p "$SSH_PORT" \
         -o ConnectTimeout=10 \
         -o StrictHostKeyChecking=accept-new \
         -o BatchMode=yes \
         "$SSH_USER@$SSH_HOST" \
         "curl -sf --max-time 10 http://localhost/health" > /dev/null 2>&1; then
      log_success "Health check prošao na $SSH_HOST!"
      return 0
    fi
    log_warn "Nema odgovora, čekam ${retry_interval}s..."
    sleep $retry_interval
  done

  log_error "Health check NEUSPJEŠAN!"
  return 1
}

# ── Rollback funkcija ─────────────────────────────────────────────────────────
rollback_local() {
  local previous_tag="${1:-}"
  log_step "Rollback (local)"

  if [[ -z "$previous_tag" ]]; then
    log_warn "Nema prethodnog taga — ne mogu rollback"
    return 1
  fi

  log_warn "Rollback na tag: $previous_tag"
  cd "$DOCKER_DIR"
  IMAGE_TAG="$previous_tag" docker compose up -d
  log_success "Rollback završen"
}

rollback_remote() {
  local previous_commit="${1:-}"
  log_step "Rollback ($ENV)"

  if [[ -z "$previous_commit" ]]; then
    log_warn "Nema prethodnog commit-a — preskačem rollback"
    return 1
  fi

  log_warn "Rollback na commit: $previous_commit"
  ssh -i "$SSH_KEY" \
      -p "$SSH_PORT" \
      -o StrictHostKeyChecking=accept-new \
      "$SSH_USER@$SSH_HOST" \
      "
        set -e
        cd '$APP_DIR'
        git checkout '$previous_commit'
        cd docker
        docker compose -f docker-compose.prod.yml up -d --build
        echo 'Rollback završen'
      "
  log_success "Rollback na $ENV završen"
}

# ── Deployment funkcije ───────────────────────────────────────────────────────
deploy_local() {
  log_step "Lokalni deploy (tag: $TAG)"
  pre_deploy_check_local

  cd "$DOCKER_DIR"

  # Čuvanje prethodnog taga za rollback
  local previous_tag
  previous_tag=$(docker compose ps --format json 2>/dev/null | \
    python3 -c "import sys,json; data=json.load(sys.stdin); print(data[0].get('Image','').split(':')[-1])" 2>/dev/null || echo "")

  log_info "Stopiranje starih servisa..."
  docker compose down --remove-orphans 2>/dev/null || true

  log_info "Build i pokretanje servisa (IMAGE_TAG=$TAG)..."
  IMAGE_TAG="$TAG" docker compose up -d --build

  log_info "Status kontejnera:"
  docker compose ps

  if ! health_check_local; then
    log_error "Deploy NEUSPJEŠAN!"
    if [[ -n "$previous_tag" ]]; then
      log_warn "Pokušavam rollback na: $previous_tag"
      rollback_local "$previous_tag"
    fi
    exit 1
  fi

  log_success "Lokalni deploy završen! ✅"
  log_info "Backend:  http://localhost:8000"
  log_info "Frontend: http://localhost:80"
  log_info "API Docs: http://localhost:8000/docs"
}

deploy_remote() {
  log_step "Remote deploy → $ENV (tag: $TAG)"

  # Postavljanje SSH varijabli
  local env_upper="${ENV^^}"
  SSH_HOST="${!${env_upper}_SSH_HOST}"
  SSH_USER="${!${env_upper}_SSH_USER}"
  SSH_KEY="${!${env_upper}_SSH_KEY}"
  SSH_PORT="${!${env_upper}_SSH_PORT:-22}"
  APP_DIR="${!${env_upper}_APP_DIR}"

  pre_deploy_check_remote

  log_info "Pokretanje deploya na $SSH_USER@$SSH_HOST..."

  # Čuvanje prethodnog commit-a za rollback
  local previous_commit
  previous_commit=$(ssh -i "$SSH_KEY" \
    -p "$SSH_PORT" \
    -o StrictHostKeyChecking=accept-new \
    -o BatchMode=yes \
    "$SSH_USER@$SSH_HOST" \
    "cd '$APP_DIR' && git rev-parse HEAD 2>/dev/null || echo ''" 2>/dev/null || echo "")

  log_info "Prethodni commit: ${previous_commit:-nepoznat}"

  # Izvršavanje deploya na serveru
  ssh -i "$SSH_KEY" \
      -p "$SSH_PORT" \
      -o StrictHostKeyChecking=accept-new \
      "$SSH_USER@$SSH_HOST" \
      "
        set -euo pipefail

        echo '→ Prelazak u direktorij projekta...'
        cd '$APP_DIR'

        echo '→ git fetch i checkout...'
        git fetch --tags origin
        if git rev-parse '$TAG' > /dev/null 2>&1; then
          git checkout '$TAG'
        else
          git reset --hard origin/main
        fi

        echo '→ docker compose pull...'
        cd docker
        docker compose -f docker-compose.prod.yml pull 2>/dev/null || true

        echo '→ Restart servisa...'
        IMAGE_TAG='$TAG' docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

        echo '→ Čišćenje starih images...'
        docker image prune -f 2>/dev/null || true

        echo '✅ Deploy komande izvršene na serveru'
      "

  if ! health_check_remote; then
    log_error "Deploy na $ENV NEUSPJEŠAN!"
    if [[ -n "$previous_commit" ]]; then
      log_warn "Automatski rollback na: $previous_commit"
      rollback_remote "$previous_commit"
    fi
    exit 1
  fi

  log_success "$ENV deploy završen! ✅"
  log_info "URL: http://$SSH_HOST"
}

# ── Glavni tok ────────────────────────────────────────────────────────────────
main() {
  log_banner
  log_info "Okruženje: ${BOLD}$ENV${NC}"
  log_info "Tag:       ${BOLD}$TAG${NC}"
  log_info "Datum:     $(date '+%Y-%m-%d %H:%M:%S')"

  validate_args

  case "$ENV" in
    local)
      deploy_local
      ;;
    staging|production)
      deploy_remote
      ;;
  esac
}

main "$@"
