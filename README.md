# 🏗️ Diagrama de Arquitetura - Macrofluxo

## Arquitetura Geral do Sistema

```mermaid
graph TB
    subgraph "Frontend - Streamlit UI"
        A[Popup Login] --> B[Sidebar Filtros]
        B --> C[Tab Gantt]
        B --> D[Tab Tabelão]
        C --> E[Visão Projeto]
        C --> F[Visão Consolidada]
    end
    
    subgraph "Componentes Customizados"
        G[dropdown_component.py]
        H[popup.py]
        I[calculate_business_days.py]
    end
    
    subgraph "Processamento de Dados"
        J[tratamento_dados_reais.py]
        K[tratamento_macrofluxo.py]
        L[app.py - load_data]
    end
    
    subgraph "Banco de Dados"
        M[(MySQL AWS RDS)]
        N[Tabela: gantt_baselines]
    end
    
    subgraph "Arquivos Locais"
        O[dados_macrofluxo_processados.csv]
        P[.env]
        Q[logoNova.svg]
    end
    
    B --> G
    A --> H
    L --> I
    
    J --> M
    K --> O
    L --> J
    L --> K
    
    C --> R[Sistema de Baselines]
    R --> N
    
    style A fill:#ff9999
    style C fill:#99ccff
    style D fill:#99ccff
    style M fill:#99ff99
    style R fill:#ffcc99
```

## Fluxo de Dados - Carregamento

```mermaid
sequenceDiagram
    participant U as Usuário
    participant P as Popup Login
    participant S as Streamlit App
    participant DB as MySQL
    participant CSV as Arquivo CSV
    participant DF as DataFrame
    
    U->>P: Acessa app
    P->>U: Solicita email
    U->>P: Fornece email
    P->>S: Autentica usuário
    
    S->>DB: Buscar dados reais
    DB-->>S: Retorna dados reais
    
    S->>CSV: Carregar dados previstos
    CSV-->>S: Retorna dados previstos
    
    S->>DF: Merge outer join
    DF->>DF: Aplicar lógica subetapas
    DF->>DF: Mapear GRUPO e SETOR
    DF-->>S: DataFrame consolidado
    
    S->>U: Renderiza interface
```

## Fluxo de Baseline

```mermaid
stateDiagram-v2
    [*] --> SemBaseline: P0 (padrão)
    
    SemBaseline --> CriarBaseline: Usuário cria snapshot
    CriarBaseline --> SalvarBanco: Gera P(n+1)
    SalvarBanco --> BaselineSalva: Sucesso
    
    BaselineSalva --> SemBaseline: Volta para P0
    BaselineSalva --> AplicarBaseline: Seleciona baseline
    
    AplicarBaseline --> VisualizarComparacao: Mostra diferenças
    VisualizarComparacao --> SemBaseline: Volta para P0
    VisualizarComparacao --> DeletarBaseline: Remove baseline
    
    DeletarBaseline --> SemBaseline
    
    note right of CriarBaseline
        Captura apenas etapas
        com dados reais
    end note
    
    note right of AplicarBaseline
        Substitui datas previstas
        pelas da baseline
    end note
```

## Estrutura de Dados - DataFrame

```mermaid
erDiagram
    DATAFRAME {
        string Empreendimento
        string UGB
        string Etapa
        date Inicio_Prevista
        date Termino_Prevista
        date Inicio_Real
        date Termino_Real
        float Percentual_Concluido
        string SETOR
        string GRUPO
    }
    
    BASELINE {
        int id PK
        string empreendimento
        string version_name
        json baseline_data
        string created_date
        timestamp created_at
        string tipo_visualizacao
    }
    
    ETAPA {
        string sigla
        string nome_completo
        string grupo
        string setor
    }
    
    SUBETAPA {
        string etapa_pai
        string subetapa
    }
    
    DATAFRAME ||--o{ ETAPA : "contém"
    ETAPA ||--o{ SUBETAPA : "pode ter"
    BASELINE ||--o{ DATAFRAME : "snapshot de"
```

## Hierarquia de Etapas

```mermaid
graph LR
    subgraph "VENDA"
        A1[PROSPEC]
        A2[LEGVENDA]
        A3[PULVENDA]
    end
    
    subgraph "LIMPEZA"
        B1[PL.LIMP]
        B2[LEG.LIMP]
        B3[ENG.LIMP]
        B3 --> B3a[PE. LIMP.]
        B3 --> B3b[ORÇ. LIMP.]
        B3 --> B3c[SUP. LIMP.]
        B4[EXECLIMP]
    end
    
    subgraph "TERRAPLANAGEM"
        C1[PL.TER]
        C2[LEG.TER]
        C3[ENG. TER]
        C3 --> C3a[PE. TER.]
        C3 --> C3b[ORÇ. TER.]
        C3 --> C3c[SUP. TER.]
        C4[EXECTER]
    end
    
    subgraph "INFRAESTRUTURA"
        D1[PL.INFRA]
        D2[LEG.INFRA]
        D3[ENG.INFRA]
        D3 --> D3a[PE. INFRA]
        D3 --> D3b[ORÇ. INFRA]
        D3 --> D3c[SUP. INFRA]
        D4[EXECINFRA]
    end
    
    subgraph "PAVIMENTAÇÃO"
        E1[ENG.PAV]
        E1 --> E1a[PE. PAV]
        E1 --> E1b[ORÇ. PAV]
        E1 --> E1c[SUP. PAV]
        E2[EXEC.PAV]
    end
    
    A1 --> A2
    A2 --> A3
    A3 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> D1
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> E1
    E1 --> E2
    
    style B3 fill:#ffcc99
    style C3 fill:#ffcc99
    style D3 fill:#ffcc99
    style E1 fill:#ffcc99
```

## Fluxo de Filtros

```mermaid
graph TD
    A[Dados Completos] --> B{Filtro UGB}
    B -->|Selecionados| C{Filtro Empreendimento}
    C -->|Selecionados| D{Filtro Grupo}
    D -->|Selecionados| E{Filtro Setor}
    E -->|Selecionados| F{Filtro Etapa}
    F -->|Todos| G[Visão Projeto]
    F -->|Específica| H[Visão Consolidada]
    
    G --> I{Pulmão Ativo?}
    H --> I
    
    I -->|Sim| J[Ajustar Datas Previstas]
    I -->|Não| K[Manter Datas]
    
    J --> L{Baseline Ativa?}
    K --> L
    
    L -->|Sim| M[Aplicar Baseline]
    L -->|Não| N[Usar P0]
    
    M --> O[Renderizar Gantt]
    N --> O
    
    style G fill:#99ccff
    style H fill:#99ccff
    style M fill:#ffcc99
    style O fill:#99ff99
```

## Componentes do Gantt

```mermaid
graph TB
    subgraph "Gantt Chart"
        A[Header Anos/Meses]
        B[Sidebar Grid]
        C[Canvas Barras]
        D[Linha Hoje]
        E[Linha Meta]
        F[Tooltips]
    end
    
    subgraph "Controles"
        G[Fullscreen]
        H[Toggle Sidebar]
        I[Filtros Flutuantes]
        J[Dropdown Baseline]
    end
    
    subgraph "Dados"
        K[Tasks Array]
        L[Baselines Object]
        M[Filter Options]
    end
    
    K --> C
    L --> J
    M --> I
    
    J --> C
    I --> C
    
    style C fill:#99ccff
    style J fill:#ffcc99
```

## Cálculo de Métricas

```mermaid
flowchart TD
    A[Dados da Etapa] --> B{Tem Datas?}
    
    B -->|Sim| C[Calcular Duração Prevista]
    B -->|Não| Z[Retornar N/D]
    
    C --> D[Calcular Duração Real]
    D --> E[Calcular VT]
    E --> F[Calcular VD]
    
    F --> G{Progress = 100?}
    
    G -->|Sim| H{Real <= Previsto?}
    G -->|Não| I{Real < Hoje?}
    
    H -->|Sim| J[Status: Verde]
    H -->|Não| K[Status: Vermelho]
    
    I -->|Sim| L[Status: Amarelo]
    I -->|Não| M[Status: Preto]
    
    J --> N[Retornar Métricas]
    K --> N
    L --> N
    M --> N
    Z --> N
    
    style J fill:#99ff99
    style K fill:#ff9999
    style L fill:#ffff99
    style M fill:#cccccc
```

## Integração de Sistemas

```mermaid
graph LR
    subgraph "Sistemas Externos"
        A[Smartsheet]
        B[Excel/CSV]
        C[Outros ERPs]
    end
    
    subgraph "ETL"
        D[tratamento_dados_reais.py]
        E[tratamento_macrofluxo.py]
    end
    
    subgraph "Armazenamento"
        F[(MySQL AWS)]
        G[Arquivos CSV]
    end
    
    subgraph "Aplicação"
        H[Streamlit App]
        I[Cache Streamlit]
    end
    
    subgraph "Saída"
        J[Gráfico Gantt]
        K[Tabelão]
        L[Baselines]
    end
    
    A --> D
    B --> E
    C --> D
    
    D --> F
    E --> G
    
    F --> H
    G --> H
    
    H --> I
    I --> J
    I --> K
    I --> L
    
    style H fill:#99ccff
    style F fill:#99ff99
    style J fill:#ffcc99
```

---

**Legenda de Cores:**
- 🔴 Vermelho: Autenticação/Login
- 🔵 Azul: Visualizações principais
- 🟢 Verde: Banco de dados/Armazenamento
- 🟠 Laranja: Sistema de baselines
- ⚪ Cinza: Processamento/Lógica
