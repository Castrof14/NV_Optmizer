# NV Optimizer 2.0

Otimizador de sistema profissional com **interface gráfica moderna** (NV brand — N azul #0011FF + V amarelo #FFEE00). Interface inspirada nos princípios visuais do design system Coinbase (dark hero, pill geometry, hairline), sem copiá-la.

## Recursos

- **Dashboard** com informações reais do computador (CPU, RAM, GPU, disco, energia, Defender, drivers).
- **Preparação**: catálogo de programas essenciais (winget), instalação do Office, limpeza/reparo do Windows e drivers.
- **Diagnóstico**: Stress Test com monitoramento em tempo real de CPU, GPU e RAM (1:00 / 5:00 / 10:00 / personalizado).
- **Otimização** em perfis **Escritório** e **Gaming** com análise real do sistema e aplicação de mudanças (serviços, energia, inicialização) + ponto de restauração.
- **Sistema**: energia (plano/tela/suspensão), Windows Defender, restauração e logs de operações.
- Barras de progresso, toasts, modais de confirmação e executores em segundo plano (thread + fila).

## Estrutura do Projeto

```
NVOptimizer/
├── main.py               # Ponto de entrada (GUI por padrão, --cli para terminal)
├── frontend/
│   ├── app.py            # Shell: janela, sidebar, header, rotas, busy, toasts
│   ├── theme.py          # Tokens NV + design system
│   ├── api.py            # Leitura de dados reais do backend
│   ├── jobs.py           # Executor em thread com fila segura (pump)
│   ├── logs.py           # Histórico de operações
│   ├── modules_bridge.py # Ações do backend expostas ao frontend
│   ├── components/       # Button, Card, Badge, Bar/PulseBar, Spinner,
│   │                     # Modal, Confirm, Toast, Loading, Error, Sidebar, Header
│   └── pages/            # dashboard, programs, office, windows, drivers,
│                         # diagnosis (stress), optimization, energy,
│                         # defender, restore, logs
├── modules/              # Backend real (system, power, security, drivers,
│                         # programs, office, diagnose, optimize, restore, ...)
├── utils/                # config, colors, logger
├── build.py              # Build PyInstaller
├── NV Optimizer.bat      # Launcher Windows (GUI)
└── requirements.txt      # Dependências
```

## Requisitos

- Python 3.8+
- `customtkinter>=6.0.0` (para compilação: `pyinstaller>=5.0`)

```bash
pip install -r requirements.txt
```

## Uso

### Executar a interface gráfica

```bash
python main.py
```

### Executar o modo terminal (legado)

```bash
python main.py --cli
```

### Compilar para executável

```bash
python build.py
```

O executável será gerado na pasta `dist/`.

## Compatibilidade

- Windows 10/11 (otimizações reais)
- macOS / Linux (dashboard e diagnóstico leem o hardware; otimizações específicas de Windows mostram "não disponível")

## Notas

- Para o melhor resultado, execute como **administrador/root** — algumas otimizações exigem elevação.
- As páginas de otimização criam um **ponto de restauração** antes de aplicar mudanças (quando possível).
- Perfis de otimização preservam itens importantes (impressoras, rede, áudio, segurança, serviços Xbox).