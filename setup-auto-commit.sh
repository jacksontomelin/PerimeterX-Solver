#!/bin/bash
# Script para configurar auto-commit automático

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║              Auto Commit - Setup Configuration                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Opção 1: GitHub Actions (Automático)
echo "[1] GitHub Actions (Recomendado)"
echo "   ✓ Automático a cada 6 horas"
echo "   ✓ Sem instalação local necessária"
echo "   ✓ Arquivo: .github/workflows/auto-commit.yml"
echo ""

# Opção 2: Cron Job Local
echo "[2] Cron Job Local"
echo "   ✓ Automático conforme agendado"
echo "   ✓ Executado localmente"
echo "   ✓ Comando: */30 * * * * cd /path && python auto_commit.py"
echo ""

# Opção 3: Git Hooks
echo "[3] Git Hooks"
echo "   ✓ Automático após cada mudança"
echo "   ✓ Sem delay"
echo "   ✓ Hooks em: .git/hooks/"
echo ""

echo "Para ativar:"
echo ""
echo "Opção 1 (GitHub Actions):"
echo "  git add .github/workflows/auto-commit.yml"
echo "  git commit -m 'ci: add auto-commit workflow'"
echo "  git push"
echo ""
echo "Opção 2 (Cron):"
echo "  crontab -e"
echo "  # Adicione a linha:"
echo "  */30 * * * * cd /path/to/repo && python auto_commit.py"
echo ""
echo "Opção 3 (Git Hooks - Já configurado):"
echo "  Apenas use: git commit"
echo "  Auto-push será executado!"
echo ""
