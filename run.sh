#!/bin/bash
# Script para instalar dependências e executar o HDR Meme Maker

cd "$(dirname "$0")"

# Verificar se Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python3 não encontrado. Por favor, instale o Python3 primeiro."
    exit 1
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
echo "Instalando dependências..."
pip install -q -r requirements.txt

# Executar o programa
echo "Iniciando HDR Meme Maker..."
python3 hdr_meme_maker.py
