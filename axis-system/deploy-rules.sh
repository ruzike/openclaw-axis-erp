#!/bin/bash

AGENTS=("coach" "draftsman" "finance" "hr" "mobile" "opps" "qc" "shket" "strategy" "tech")
RULES_SRC="/tmp/openclaw-superagent/workspace/HONESTY-RULES.md"
SEC_SRC="/tmp/openclaw-superagent/workspace/SECURITY-RULES.md"

for AGENT in "${AGENTS[@]}"; do
    DIR="/home/axis/openclaw/agents/$AGENT"
    if [ -d "$DIR" ]; then
        echo "Deploying to $AGENT..."
        
        # 1. Copy rule files
        cp "$RULES_SRC" "$DIR/HONESTY-RULES.md"
        cp "$SEC_SRC" "$DIR/SECURITY-RULES.md"
        
        # 2. Create memory structure
        mkdir -p "$DIR/memory/core"
        touch "$DIR/memory/patterns.md"
        touch "$DIR/memory/lessons-learned.md"
        
        # 3. Inject reference into SOUL.md if it exists and doesn't already have it
        if [ -f "$DIR/SOUL.md" ]; then
            if ! grep -q "ПРАВИЛА ЧЕСТНОСТИ И БЕЗОПАСНОСТИ" "$DIR/SOUL.md"; then
                cat >> "$DIR/SOUL.md" << 'INNEREOF'

## 📜 ПРАВИЛА ЧЕСТНОСТИ И БЕЗОПАСНОСТИ
- Изучай `HONESTY-RULES.md` и `SECURITY-RULES.md` в корне рабочей директории.
- Не выдумывай. Сначала делай, потом пиши. Не молчи больше 30 секунд.
- Ошибся — признай. Ошибка 3+ раз мигрирует в `memory/patterns.md` → `memory/lessons-learned.md`.
INNEREOF
            fi
        fi
    fi
done
echo "✅ Раскатано на всех агентов!"
