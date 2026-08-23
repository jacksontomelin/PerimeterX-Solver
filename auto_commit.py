#!/usr/bin/env python3
"""
Auto Commit Script - PerimeterX Solver
Faz commit automático de mudanças
"""

import subprocess
import os
from datetime import datetime
import sys

def run_command(cmd, description=""):
    """Execute comando e retorna resultado"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Erro: {description}")
            print(f"   {result.stderr}")
            return False
        if result.stdout:
            print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ Erro ao executar: {e}")
        return False

def check_changes():
    """Verifica se há mudanças"""
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    return bool(result.stdout.strip())

def auto_commit():
    """Faz auto-commit"""
    
    print("="*70)
    print("  Auto Commit - PerimeterX Solver")
    print("="*70)
    print()
    
    # Verificar se é um repositório git
    if not os.path.exists(".git"):
        print("❌ Não é um repositório Git!")
        return False
    
    # Configurar git
    print("[1] Configurando Git...")
    run_command('git config user.email "auto@script.local"', "Email configurado")
    run_command('git config user.name "Auto Commit"', "Nome configurado")
    
    # Verificar mudanças
    print("\n[2] Verificando mudanças...")
    if not check_changes():
        print("✅ Nenhuma mudança detectada")
        return True
    
    # Stage all changes
    print("\n[3] Adicionando mudanças...")
    if not run_command("git add -A", "Mudanças adicionadas"):
        return False
    
    # Commit
    print("\n[4] Fazendo commit...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"chore: auto-commit {timestamp}"
    
    if not run_command(f'git commit -m "{commit_msg}"', "Commit realizado"):
        return False
    
    # Push
    print("\n[5] Enviando para GitHub...")
    if not run_command("git push", "Push realizado"):
        return False
    
    print("\n" + "="*70)
    print("✅ Auto-commit concluído com sucesso!")
    print("="*70)
    
    return True

if __name__ == "__main__":
    success = auto_commit()
    sys.exit(0 if success else 1)
