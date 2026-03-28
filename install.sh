#!/bin/bash

# ============================================================
#  AXIS ERP — Интерактивный установщик
#  https://github.com/ruzike/openclaw-axis-erp
# ============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

print_header() {
  echo ""
  echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║         AXIS ERP — Установщик           ║${NC}"
  echo -e "${BOLD}${CYAN}║   12 AI-агентов для вашего бизнеса      ║${NC}"
  echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${NC}"
  echo ""
}

ask() {
  local prompt="$1"
  local var="$2"
  local default="$3"
  echo -e "${YELLOW}▶ ${prompt}${NC}"
  if [ -n "$default" ]; then
    echo -e "  ${BLUE}(Enter для пропуска / оставить пустым)${NC}"
  fi
  read -r "$var"
}

ask_required() {
  local prompt="$1"
  local var="$2"
  while true; do
    echo -e "${YELLOW}▶ ${prompt}${NC}"
    read -r value
    if [ -n "$value" ]; then
      eval "$var='$value'"
      break
    else
      echo -e "${RED}  Это поле обязательно!${NC}"
    fi
  done
}

print_step() {
  echo ""
  echo -e "${BOLD}${GREEN}━━━ Шаг $1: $2 ━━━${NC}"
  echo ""
}

# ── START ──────────────────────────────────────────────────
print_header

# ── Определяем режим ──────────────────────────────────────
INSTALL_DIR="${HOME}/openclaw"
OPENCLAW_DIR="${HOME}/.openclaw"
CONFIG_EXISTS=false
AGENTS_EXIST=false

[ -f "${OPENCLAW_DIR}/openclaw.json" ] && CONFIG_EXISTS=true
[ -d "${INSTALL_DIR}/agents" ] && AGENTS_EXIST=true

if $CONFIG_EXISTS || $AGENTS_EXIST; then
  echo -e "${YELLOW}⚠️  Обнаружена существующая установка AXIS:${NC}"
  $CONFIG_EXISTS && echo -e "   ${GREEN}✓${NC} openclaw.json найден"
  $AGENTS_EXIST  && echo -e "   ${GREEN}✓${NC} Агенты найдены в ${INSTALL_DIR}/agents"
  echo ""
  echo -e "Выбери режим:"
  echo -e "  ${BOLD}1${NC} — Полная установка (перезапишет всё)"
  echo -e "  ${BOLD}2${NC} — Обновить только агентов (SOUL.md, AGENTS.md, TOOLS.md) — конфиг не трогать"
  echo -e "  ${BOLD}3${NC} — Добавить только новых агентов (существующих не трогать)"
  echo -e "  ${BOLD}4${NC} — Выход"
  echo ""
  read -rp "Введи номер [1-4]: " MODE
  echo ""
else
  MODE="1"
fi

case "$MODE" in
  2)
    echo -e "${CYAN}Режим: Обновление промптов агентов${NC}"
    echo ""
    for agent_dir in ./agents/*/; do
      agent=$(basename "$agent_dir")
      target="${INSTALL_DIR}/agents/${agent}"
      if [ -d "$target" ]; then
        for f in SOUL.md AGENTS.md TOOLS.md IDENTITY.md HEARTBEAT.md; do
          [ -f "${agent_dir}${f}" ] && cp "${agent_dir}${f}" "${target}/${f}"
        done
        echo -e "  ${GREEN}✓${NC} ${agent} — промпты обновлены (MEMORY.md и memory/ сохранены)"
      else
        cp -r "$agent_dir" "${INSTALL_DIR}/agents/"
        echo -e "  ${BLUE}+${NC} ${agent} — добавлен новый агент"
      fi
    done
    echo ""
    echo -e "${GREEN}✅ Промпты агентов обновлены. openclaw.json не изменён.${NC}"
    echo -e "Перезапусти OpenClaw: ${CYAN}openclaw restart${NC}"
    exit 0
    ;;
  3)
    echo -e "${CYAN}Режим: Добавление новых агентов${NC}"
    echo ""
    for agent_dir in ./agents/*/; do
      agent=$(basename "$agent_dir")
      target="${INSTALL_DIR}/agents/${agent}"
      if [ -d "$target" ]; then
        echo -e "  ${YELLOW}~${NC} ${agent} — уже существует, пропускаю"
      else
        cp -r "$agent_dir" "${INSTALL_DIR}/agents/"
        echo -e "  ${BLUE}+${NC} ${agent} — добавлен"
      fi
    done
    echo ""
    echo -e "${GREEN}✅ Новые агенты добавлены.${NC}"
    echo -e "Добавь их в openclaw.json вручную или запусти режим 1 для полной переустановки."
    exit 0
    ;;
  4)
    echo "Выход."; exit 0 ;;
  *)
    echo -e "${CYAN}Режим: Полная установка${NC}"
    ;;
esac

echo -e "Этот скрипт настроит всех 12 агентов AXIS на твоём сервере."
echo -e "Занимает около ${BOLD}5-10 минут${NC}."
echo ""
echo -e "Нажми ${BOLD}Enter${NC} чтобы начать..."
read -r

# ── ШАГ 1: Базовые данные ─────────────────────────────────
print_step "1" "Ваш Telegram"

echo -e "  Узнать свой Telegram ID: напиши ${CYAN}/start${NC} боту ${CYAN}@userinfobot${NC}"
echo ""
ask_required "Введи свой Telegram ID (только цифры, например: 110440505):" TELEGRAM_ID

echo ""
echo -e "${GREEN}✓ Telegram ID: ${TELEGRAM_ID}${NC}"

# ── ШАГ 2: API ключи ──────────────────────────────────────
print_step "2" "API ключи для AI моделей"

echo -e "  Получить ключ Anthropic: ${CYAN}https://console.anthropic.com${NC}"
echo -e "  Получить ключ OpenAI:    ${CYAN}https://platform.openai.com${NC}"
echo ""

ask_required "Введи Anthropic API ключ (sk-ant-api03-...):" ANTHROPIC_KEY

echo ""
ask "Введи OpenAI API ключ (sk-...) [опционально]:" OPENAI_KEY ""

# ── ШАГ 3: URL сервера ────────────────────────────────────
print_step "3" "URL сервера"

echo -e "  Если у тебя есть домен: ${CYAN}https://api.yourdomain.com${NC}"
echo -e "  Если нет — оставь пустым (настроишь позже)"
echo ""
ask "Введи URL твоего OpenClaw Gateway:" GATEWAY_URL ""

if [ -z "$GATEWAY_URL" ]; then
  GATEWAY_URL="https://api.yourdomain.com"
fi

# ── ШАГ 4: Telegram боты ──────────────────────────────────
print_step "4" "Токены Telegram ботов"

echo -e "  Создай ботов через ${CYAN}@BotFather${NC} → /newbot"
echo -e "  Подробнее: см. ${CYAN}SETUP.md${NC}"
echo ""

AGENTS=("main" "devops" "hr" "finance" "sales" "ops" "qc" "tech" "strategy" "coach" "shket" "draftsman")
declare -A BOT_TOKENS

for agent in "${AGENTS[@]}"; do
  ask "Токен бота для агента '${agent}' [Enter чтобы пропустить]:" token ""
  BOT_TOKENS[$agent]="$token"
done

# ── ШАГ 5: Установка ──────────────────────────────────────
print_step "5" "Установка файлов"

INSTALL_DIR="${HOME}/openclaw"
echo -e "  Папка установки: ${CYAN}${INSTALL_DIR}${NC}"
echo ""

# Создаём структуру директорий
mkdir -p "$INSTALL_DIR"

# Копируем агентов
if [ -d "./agents" ]; then
  echo -e "  ${GREEN}→${NC} Копирую агентов..."
  cp -r ./agents "$INSTALL_DIR/"

  # Заменяем плейсхолдеры Telegram ID
  find "$INSTALL_DIR/agents" -type f -name "*.md" -o -name "*.json" -o -name "*.py" | \
    xargs grep -l "YOUR_TELEGRAM_ID" 2>/dev/null | \
    xargs sed -i "s/YOUR_TELEGRAM_ID/${TELEGRAM_ID}/g" 2>/dev/null || true

  find "$INSTALL_DIR/agents" -type f | \
    xargs grep -l "110440505\|465267540" 2>/dev/null | \
    xargs sed -i "s/110440505/${TELEGRAM_ID}/g; s/465267540/${TELEGRAM_ID}/g" 2>/dev/null || true

  echo -e "  ${GREEN}✓${NC} Агенты скопированы"
fi

# Копируем системные скрипты
for dir in axis-system knowledge scripts; do
  if [ -d "./$dir" ]; then
    echo -e "  ${GREEN}→${NC} Копирую ${dir}..."
    cp -r "./$dir" "$INSTALL_DIR/"
    echo -e "  ${GREEN}✓${NC} ${dir} скопирован"
  fi
done

# Копируем dashboard
if [ -d "./dashboard" ]; then
  cp -r ./dashboard "$INSTALL_DIR/"
  echo -e "  ${GREEN}✓${NC} Dashboard скопирован"
fi

# ── ШАГ 6: Генерация openclaw.json ────────────────────────
print_step "6" "Генерация конфигурации OpenClaw"

OPENCLAW_DIR="${HOME}/.openclaw"
mkdir -p "$OPENCLAW_DIR"

# Генерируем случайный токен
GATEWAY_TOKEN=$(openssl rand -base64 32 | tr -d '=/+' | head -c 43)

# Строим секцию accounts
ACCOUNTS_JSON=""
for agent in "${AGENTS[@]}"; do
  token="${BOT_TOKENS[$agent]}"
  if [ -n "$token" ]; then
    ACCOUNTS_JSON="${ACCOUNTS_JSON}
            \"${agent}\": {
              \"dmPolicy\": \"allowlist\",
              \"botToken\": \"${token}\",
              \"allowFrom\": [${TELEGRAM_ID}],
              \"streaming\": \"partial\"
            },"
  fi
done

# Генерируем bindings
BINDINGS_JSON=""
for agent in "${AGENTS[@]}"; do
  if [ -n "${BOT_TOKENS[$agent]}" ]; then
    BINDINGS_JSON="${BINDINGS_JSON}
        {\"agentId\": \"${agent}\", \"match\": {\"channel\": \"telegram\", \"accountId\": \"${agent}\"}},  "
  fi
done

cat > "${OPENCLAW_DIR}/openclaw.json" << EOFJSON
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "anthropic/claude-sonnet-4-5"
      },
      "workspace": "${INSTALL_DIR}"
    },
    "list": [
      $(for agent in "${AGENTS[@]}"; do echo "{\"id\": \"${agent}\", \"workspace\": \"${INSTALL_DIR}/agents/${agent}\"},"; done)
      {"id": "placeholder"}
    ]
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {
      "mode": "token",
      "token": "${GATEWAY_TOKEN}"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "allowFrom": [${TELEGRAM_ID}],
      "accounts": {
        $(for agent in "${AGENTS[@]}"; do
          token="${BOT_TOKENS[$agent]}"
          if [ -n "$token" ]; then
            echo "\"${agent}\": {\"botToken\": \"${token}\", \"allowFrom\": [${TELEGRAM_ID}], \"dmPolicy\": \"allowlist\"},"
          fi
        done)
        "placeholder": {}
      }
    }
  },
  "bindings": [
    $(for agent in "${AGENTS[@]}"; do
      if [ -n "${BOT_TOKENS[$agent]}" ]; then
        echo "{\"agentId\": \"${agent}\", \"match\": {\"channel\": \"telegram\", \"accountId\": \"${agent}\"}},"
      fi
    done)
    {"agentId": "main", "match": {"channel": "telegram", "accountId": "placeholder"}}
  ]
}
EOFJSON

echo -e "  ${GREEN}✓${NC} openclaw.json создан"

# ── ШАГ 7: Env secrets ────────────────────────────────────
cat > "${OPENCLAW_DIR}/env-secrets" << EOFENV
ANTHROPIC_API_KEY=${ANTHROPIC_KEY}
$([ -n "$OPENAI_KEY" ] && echo "OPENAI_API_KEY=${OPENAI_KEY}")
EOFENV
chmod 600 "${OPENCLAW_DIR}/env-secrets"
echo -e "  ${GREEN}✓${NC} env-secrets создан (права 600)"

# ── ФИНАЛ ─────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║           ✅ Установка завершена!        ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BOLD}Следующие шаги:${NC}"
echo ""
echo -e "  1. Запусти OpenClaw:"
echo -e "     ${CYAN}openclaw start${NC}"
echo ""
echo -e "  2. Напиши ${CYAN}/start${NC} своему главному боту в Telegram"
echo ""
echo -e "  3. Gateway токен (сохрани!):"
echo -e "     ${YELLOW}${GATEWAY_TOKEN}${NC}"
echo ""
echo -e "  4. Подробная документация: ${CYAN}SETUP.md${NC}"
echo ""
echo -e "${BLUE}Удачи! AXIS работает 24/7 🚀${NC}"
echo ""
