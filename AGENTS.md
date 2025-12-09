# AGENTS.md - Technical Documentation

## Project Overview

**Project Name:** Baseline Macrofluxo Dashboard v2  
**Type:** Real Estate Development Project Management Dashboard  
**Primary Technology:** Streamlit (Python Web Application)  
**License:** MIT License (2025 V&M-planejamento)  
**Purpose:** Interactive Gantt chart visualization and project tracking system for real estate development stages

---

## Architecture Overview

This is a **Streamlit-based web application** that provides comprehensive project management visualization for real estate development projects. The system integrates multiple data sources (Smartsheet API, MySQL, Excel) to create interactive Gantt charts and data tables for tracking project stages across different developments.

### Core Components

```
baseline.mf.v2/
├── app.py (6036 lines)              # Main application controller
├── dropdown_component.py (322 lines) # Custom multi-select dropdown UI
├── popup.py (163 lines)             # Welcome screen component
├── calculate_business_days.py       # Business days calculation utility
├── tratamento_dados_reais.py        # Real-time data processing (Smartsheet API)
├── tratamento_macrofluxo.py         # Forecast data processing (Excel)
├── tratamento_mysql.py              # MySQL database operations
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables (Smartsheet token)
├── style.css                        # Custom CSS styling
└── GRÁFICO MACROFLUXO.xlsx         # Source Excel file for forecasted data
```

---

## Technology Stack

### Core Framework
- **Streamlit 1.46.1** - Web application framework
- **Python 3.x** - Base programming language

### Data Processing & Visualization
- **Pandas 2.3.1** - Data manipulation and analysis
- **NumPy 2.2.6** - Numerical computing
- **Matplotlib 3.10.3** - Static plotting library
- **Plotly 6.1.2** - Interactive visualizations
- **Seaborn 0.13.2** - Statistical data visualization
- **Altair 5.5.0** - Declarative visualization

### Database & Data Sources
- **MySQL Connector Python 8.0.0+** - MySQL database connectivity
- **Smartsheet Python SDK 3.0.5** - Smartsheet API integration
- **openpyxl 3.1.5** - Excel file processing

### Date & Time Handling
- **python-dateutil 2.9.0** - Advanced date operations
- **holidays 0.83** - Holiday calendar support
- **pytz 2025.2** - Timezone support

### Web & API
- **requests 2.32.4** - HTTP library
- **Flask 3.1.1** - Web framework (auxiliary)
- **beautifulsoup4 4.13.4** - HTML parsing

### Configuration & Environment
- **python-dotenv 1.1.1** - Environment variable management
- **python-decouple 3.8** - Settings management

### Development Tools
- **ipython 9.3.0** - Interactive Python shell
- **GitPython 3.1.44** - Git repository interaction

---

## Data Model

### Stage Definitions (34 Stages)

The system tracks 34 distinct project stages organized in a predefined sequence:

```python
ORDEM_ETAPAS_GLOBAL = [
    "PROSPEC",      # Prospection
    "LEGVENDA",     # Sales Legalization
    "PULVENDA",     # Sales Buffer
    "PL.LIMP",      # Cleaning Planning
    "LEG.LIMP",     # Cleaning Legalization
    "ENG.LIMP",     # Cleaning Engineering
    "PE. LIMP.",    # Cleaning Project
    "ORÇ. LIMP.",   # Cleaning Budget
    "SUP. LIMP.",   # Cleaning Supervision
    "EXECLIMP",     # Cleaning Execution
    "PL.TER",       # Earthwork Planning
    "LEG.TER",      # Earthwork Legalization
    "ENG. TER",     # Earthwork Engineering
    "PE. TER.",     # Earthwork Project
    "ORÇ. TER.",    # Earthwork Budget
    "SUP. TER.",    # Earthwork Supervision
    "EXECTER",      # Earthwork Execution
    "PL.INFRA",     # Infrastructure Planning
    "LEG.INFRA",    # Infrastructure Legalization
    "ENG.INFRA",    # Infrastructure Engineering
    "PE. INFRA",    # Infrastructure Project
    "ORÇ. INFRA",   # Infrastructure Budget
    "SUP. INFRA",   # Infrastructure Supervision
    "EXECINFRA",    # Infrastructure Execution
    "ENG.PAV",      # Paving Engineering
    "PE. PAV",      # Paving Project
    "ORÇ. PAV",     # Paving Budget
    "SUP. PAV",     # Paving Supervision
    "EXEC.PAV",     # Paving Execution
    "PUL.INFRA",    # Infrastructure Buffer
    "PL.RAD",       # Radier Planning
    "LEG.RAD",      # Radier Legalization
    "PUL.RAD",      # Radier Buffer
    "RAD",          # Radier
    "DEM.MIN",      # Minimum Demand
    "PE. ÁREAS COMUNS (URB)",    # Common Areas Project (Urban)
    "PE. ÁREAS COMUNS (ENG)",    # Common Areas Project (Engineering)
    "ORÇ. ÁREAS COMUNS",          # Common Areas Budget
    "SUP. ÁREAS COMUNS",          # Common Areas Supervision
    "EXECUÇÃO ÁREAS COMUNS"       # Common Areas Execution
]
```

### Groups (7 Categories)

Stages are organized into functional groups:

1. **VENDA** (Sales) - Prospection, sales legalization, sales buffer
2. **LIMPEZA** (Cleaning) - All cleaning-related stages
3. **TERRAPLANAGEM** (Earthwork) - All earthwork stages
4. **INFRA INCIDENTE** (Infrastructure) - All infrastructure stages
5. **PAVIMENTAÇÃO** (Paving) - All paving stages
6. **PULMÃO** (Buffer) - Buffer periods
7. **RADIER** - Radier foundation stages
8. **DM** (Minimum Demand) - Minimum demand milestone
9. **EQUIPANENTOS COMUNS** (Common Equipment) - Common area stages

### Sectors (8 Categories)

Stages are also categorized by organizational sector:

1. **PROSPECÇÃO** - Prospection
2. **LEGALIZAÇÃO** - Legal processes
3. **PULMÃO** - Buffer management
4. **ENGENHARIA** - Engineering tasks
5. **INFRA** - Infrastructure execution
6. **PRODUÇÃO** - Production (Radier)
7. **ARQUITETURA & URBANISMO** - Architecture & Urban Planning
8. **VENDA** - Sales (Minimum Demand)

### Sub-stages Hierarchy

Four main stages have sub-stages that are tracked separately:

```python
SUBETAPAS = {
    "ENG. LIMP.": ["PE. LIMP.", "ORÇ. LIMP.", "SUP. LIMP."],
    "ENG. TER.": ["PE. TER.", "ORÇ. TER.", "SUP. TER."],
    "ENG. INFRA": ["PE. INFRA", "ORÇ. INFRA", "SUP. INFRA"],
    "ENG. PAV": ["PE. PAV", "ORÇ. PAV", "SUP. PAV"]
}
```

Where:
- **PE** = Projeto (Project)
- **ORÇ** = Orçamento (Budget)
- **SUP** = Supervisão (Supervision)

### Data Structure

Each project stage contains:

```python
{
    "Empreendimento": str,      # Development name
    "Etapa": str,               # Stage name (abbreviated)
    "Inicio_Prevista": datetime, # Forecasted start date
    "Termino_Prevista": datetime, # Forecasted end date
    "Inicio_Real": datetime,    # Actual start date
    "Termino_Real": datetime,   # Actual end date
    "% concluído": float,       # Completion percentage (0-100)
    "UGB": str,                 # Business Unit (Unidade de Gestão de Negócios)
    "SETOR": str,               # Sector classification
    "GRUPO": str                # Group classification
}
```

---

## Color Scheme & Styling

### Sector-Based Colors

Each sector has distinct color palettes for forecasted vs. actual data:

```python
CORES_POR_SETOR = {
    "PROSPECÇÃO": {"previsto": "#FEEFC4", "real": "#AE8141"},
    "LEGALIZAÇÃO": {"previsto": "#fadbfe", "real": "#BF08D3"},
    "PULMÃO": {"previsto": "#E9E8E8", "real": "#535252"},
    "ENGENHARIA": {"previsto": "#fbe3cf", "real": "#be5900"},
    "INFRA": {"previsto": "#daebfb", "real": "#125287"},
    "PRODUÇÃO": {"previsto": "#E1DFDF", "real": "#252424"},
    "ARQUITETURA & URBANISMO": {"previsto": "#D4D3F9", "real": "#453ECC"},
    "VENDA": {"previsto": "#dffde1", "real": "#096710"}
}
```

### Status Indicators

- **Green** - Completed on time (100% complete, actual end ≤ forecasted end)
- **Red** - Completed late (100% complete, actual end > forecasted end)
- **Yellow** - In progress but behind schedule (< 100% complete, actual end date passed)
- **Black** - Default status

---

## Data Sources

### 1. Smartsheet API (Real-Time Data)

**File:** `tratamento_dados_reais.py`

- **Purpose:** Fetches actual project data from Smartsheet reports
- **API:** Smartsheet SDK v3.0.5
- **Authentication:** Access token stored in `.env` file
- **Report Name:** "Relatório MF- Smart"
- **Output Format:** CSV → DataFrame with unpivot transformation

**Key Functions:**
- `buscar_e_processar_dados_completos()` - Master function for full pipeline
- `get_report_id(client, report_name)` - Retrieves report ID by name
- `get_report_data(client, report_id)` - Downloads CSV and converts to DataFrame
- `processar_dados_macrofluxo(df)` - Unpivots data (columns → rows transformation)

### 2. Excel File (Forecasted Data)

**File:** `tratamento_macrofluxo.py`

- **Source File:** `GRÁFICO MACROFLUXO.xlsx`
- **Sheet:** "GERAL"
- **Header Row:** Line 7 (index 6)
- **Excluded Projects:** 'JARDIM DAS HOTÊNSIAS', 'RECANTO DAS OLIVEIRAS'

**Key Functions:**
- `tratar_macrofluxo()` - Main processing function
- Unpivots date columns (ETAPA.TIPO.INICIO_FIM format)
- Filters only 'PREV' (forecasted) data
- Handles special cases like "EXECUÇÃO ÁREAS COMUNS"

### 3. MySQL Database (Baselines & Historical Data)

**File:** `tratamento_mysql.py`

- **Database:** AWS MySQL
- **Configuration:** Retrieved from `st.secrets["aws_db"]`
- **Main Table:** `gantt_baselines`

**Table Schema:**
```sql
CREATE TABLE gantt_baselines (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empreendimento VARCHAR(255) NOT NULL,
    version_name VARCHAR(255) NOT NULL,
    baseline_data JSON NOT NULL,
    created_date VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_visualizacao VARCHAR(50) NOT NULL,
    UNIQUE KEY unique_baseline (empreendimento, version_name)
)
```

**Key Functions:**
- `create_baselines_table()` - Initializes baseline table
- `save_baseline()` - Saves snapshot with ON DUPLICATE KEY UPDATE
- `load_baselines()` - Retrieves all baselines grouped by development
- `delete_baseline()` - Removes specific baseline version
- `take_gantt_baseline()` - Creates baseline snapshot from current state

---

## Application Flow

### Initialization Sequence

```
1. Import Dependencies
   ├── Core libraries (streamlit, pandas, numpy, matplotlib)
   ├── Custom components (dropdown_component, popup, calculate_business_days)
   └── Data processors (tratamento_dados_reais, tratamento_macrofluxo)

2. Global Configuration
   ├── Define ORDEM_ETAPAS_GLOBAL (34 stages)
   ├── Define GRUPOS (7 groups)
   ├── Define SETOR (8 sectors)
   ├── Create mappings (sigla ↔ nome_completo)
   └── Initialize StyleConfig with colors

3. Database Setup
   ├── Load DB_CONFIG from st.secrets or use mock data
   ├── Create gantt_baselines table if not exists
   └── Initialize session state variables

4. Welcome Screen
   ├── show_welcome_screen() displays fullscreen popup
   ├── User clicks "Acessar Painel" button
   └── Clear query params and proceed

5. Data Loading (Cached)
   ├── IF MODO_REAL == True:
   │   ├── buscar_e_processar_dados_completos() → df_real
   │   └── tratar_macrofluxo() → df_previsto
   ├── ELSE: criar_dados_exemplo()
   └── Merge df_real + df_previsto → df_merged

6. UI Rendering
   ├── Sidebar Filters
   │   ├── UGB (Business Unit)
   │   ├── Empreendimento (Development)
   │   ├── Grupo (Group)
   │   ├── Setor (Sector)
   │   ├── Etapa (Stage)
   │   ├── Pulmão Simulation (Buffer months)
   │   └── Data type selection (Forecast/Real/Both)
   └── Main Content (Tabs)
       ├── Tab 1: Gantt Chart
       │   ├── Project View (all stages per development)
       │   └── Consolidated View (single stage across developments)
       └── Tab 2: Data Table
           ├── Hierarchical Layout (multiple stages)
           └── Horizontal Pivot Layout (single stage)
```

### Gantt Chart Generation

**Two Visualization Modes:**

#### 1. Project View (`gerar_gantt_por_projeto`)

- Shows all filtered stages for each development
- Interactive HTML/JavaScript implementation
- Features:
  - Expandable/collapsible sub-stages
  - Virtual Select dropdowns for filtering
  - Fullscreen mode toggle
  - Sidebar with 10 columns (stage name, dates, durations, variations)
  - Timeline chart with month/year headers
  - "Today" line and "Meta Assinatura" (signature goal) line
  - Tooltips showing detailed information
  - Forecast (light) and actual (dark) bars with overlap

#### 2. Consolidated View (`gerar_gantt_consolidado`)

- Compares single stage across multiple developments
- Groups data by stage and development
- JavaScript allows switching stages without reloading
- Same visual features as Project View

**Visual Elements:**

```javascript
Components:
├── Sidebar Grid (10 columns)
│   ├── Nº (Number)
│   ├── Etapa (Stage)
│   ├── Início Prev (Forecasted Start)
│   ├── Término Prev (Forecasted End)
│   ├── Dur.Prev (Forecasted Duration in months)
│   ├── Início Real (Actual Start)
│   ├── Término Real (Actual End)
│   ├── Dur.Real (Actual Duration in months)
│   ├── % (Completion percentage)
│   └── VT (Variation of Termination in business days)
│
├── Timeline Chart
│   ├── Header (Years/Months)
│   ├── Bars
│   │   ├── Forecast (sector light color, opacity 0.3)
│   │   └── Actual (sector dark color, solid)
│   ├── Lines
│   │   ├── Today line (red dashed)
│   │   └── Meta line (blue dashed with diamond markers)
│   └── Tooltips
│       ├── Stage name
│       ├── Dates (forecast vs actual)
│       ├── Duration (forecast vs actual)
│       ├── Variation metrics (VT, VD)
│       └── Completion percentage
│
└── Controls
    ├── Fullscreen toggle
    ├── Sidebar visibility toggle
    └── Virtual Select filters (Setor, Grupo)
```

### Data Table Generation

**Two Layout Modes:**

#### 1. Hierarchical Layout (Multiple Stages)

```
Development A (Header with totals/averages)
├── Stage 1 (indented)
├── Stage 2 (indented)
└── Stage 3 (indented)

Development B (Header with totals/averages)
├── Stage 1 (indented)
└── Stage 2 (indented)
```

Columns:
- Development / Stage
- Forecasted Start/End
- Actual Start/End
- Forecast Duration (days/months)
- Actual Duration (days/months)
- Variation (VT, VD)
- Completion %
- Status

#### 2. Horizontal Pivot Layout (Single Stage)

- Stages as columns
- MultiIndex columns: [Stage][Date/Duration metrics]
- Sortable by 5 different criteria
- Columns ordered by ORDEM_ETAPAS_GLOBAL

**Conditional Formatting:**

- **Green text:** Completed on time
- **Red text:** Completed late
- **Yellow text:** In progress but behind
- **Black text:** Default
- Variation arrows: ▲ (late) / ▼ (early)

---

## Key Features

### 1. Buffer (Pulmão) Simulation

Allows users to simulate timeline adjustments by adding buffer months:

**Logic:**
- Buffer stages (PULVENDA, PUL.INFRA, PUL.RAD): Adjust only termination dates
- Protected stages (PROSPEC, RAD, DEM.MIN): No changes
- Other stages: Shift both start and end dates

**Implementation:** `ajustar_datas_com_pulmao(df, meses_pulmao)`

### 2. Business Days Calculation

**Function:** `calculate_business_days(start_date, end_date)`

- Uses `np.busday_count()` for accurate business day counting
- Considers holidays (via `holidays` library)
- Used for variation metrics (VT, VD)

**Metrics:**
- **VT** (Variação de Término) = Variation in termination date (business days)
- **VD** (Variação de Duração) = Variation in duration (business days)

### 3. Baseline Management

Baselines are snapshots of project timelines at specific points:

**Workflow:**
1. User triggers baseline creation via context menu
2. System captures current state of all stages for a development
3. Generates version name (e.g., P1, P2, P3...)
4. Stores in MySQL as JSON with metadata:
   - Development name
   - Version name
   - Baseline data (tasks with dates and completion %)
   - Creation date
   - Visualization type (Gantt)

**Functions:**
- `take_gantt_baseline(df, empreendimento, tipo_visualizacao)`
- `process_context_menu_actions()` - Handles URL-based triggers
- `process_baseline_change()` - Switches between baseline views

### 4. Sub-stage Expansion

Engineering stages have expandable sub-stages:

**Parent-Child Relationship:**
- Parent stage dates = MIN(sub-stage starts) to MAX(sub-stage ends)
- Parent progress = AVERAGE(sub-stage progress)
- Sub-stages show only actual data (no forecast)

**UI Implementation:**
- JavaScript toggle function
- CSS classes: `.substage`, `.substage-hidden`
- Expand/collapse icons next to parent stages

### 5. Dynamic Filtering

Multi-level cascading filters:

```
UGB Filter
  └→ Empreendimento Filter
      └→ Grupo Filter
          └→ Setor Filter
              └→ Etapa Filter
```

Each filter updates available options in downstream filters.

### 6. Date Period Calculation

**Function:** `calcular_periodo_datas(df, meses_padding_inicio, meses_padding_fim)`

- Analyzes all dates in filtered dataset
- Adds padding (default: 1 month before, 36 months after)
- Ensures month boundaries (first day to last day)
- Used to set Gantt chart timeline bounds

---

## Utility Functions

### Date & Time

- `calcular_dias_uteis_novo(data_inicio, data_fim)` - Business days with sign handling
- `converter_porcentagem(valor)` - Handles both 0-1 and 0-100 formats
- `obter_data_meta_assinatura_novo(df_empreendimento)` - Extracts "Minimum Demand" milestone date

### Data Transformation

- `padronizar_etapa(etapa_original)` - Maps stage names to standardized format
- `converter_dados_para_gantt(df)` - Transforms DataFrame to Gantt-compatible JSON
- `processar_dados_macrofluxo(df)` - Unpivots Excel/Smartsheet data

### UI Components

- `simple_multiselect_dropdown()` - Custom multi-select with search and "Select All"
- `show_welcome_screen()` - Fullscreen branded popup with responsive button

---

## Configuration Files

### `.env`
```
SMARTSHEET_ACCESS_TOKEN=<your_token_here>
```

### `requirements.txt`
Contains 110+ dependencies (see full list in file)

Key highlights:
- streamlit>=1.28.0
- pandas>=1.5.0
- mysql-connector-python>=8.0.0
- matplotlib==3.10.3
- numpy==2.2.6
- smartsheet-python-sdk==3.0.5
- holidays==0.83

### Streamlit Secrets (Production)

Expected structure:
```toml
[aws_db]
host = "your-aws-endpoint.rds.amazonaws.com"
user = "database_user"
password = "database_password"
database = "database_name"
```

---

## Session State Variables

```python
st.session_state = {
    'current_baseline': str,           # Currently selected baseline version
    'current_baseline_data': dict,     # Data for current baseline
    'current_empreendimento': str,     # Currently selected development
    'show_popup': bool,                # Welcome screen visibility flag
    'mock_baselines': dict,            # Fallback storage when DB unavailable
    
    # Dropdown component states (dynamic, per filter)
    f'{key}_search': str,              # Search query
    f'{key}_select_all': bool,         # Select all checkbox state
    f'{key}_checkbox_{option}': bool,  # Individual option checkboxes
}
```

---

## API Integration

### Smartsheet API

**Authentication:** Bearer token from environment variable

**Endpoints Used:**
- `GET /reports` - List all accessible reports
- `GET /reports/{reportId}` - Download report as CSV

**Error Handling:**
- Try-catch with fallback to mock data
- Detailed traceback printing for debugging
- Graceful degradation if API unavailable

### MySQL Database

**Connection Parameters:**
- Host, User, Password, Database from Streamlit secrets
- Port: 3306 (default MySQL)

**Operations:**
- INSERT with ON DUPLICATE KEY UPDATE (upsert pattern)
- JSON serialization with `ensure_ascii=False`
- Connection pooling (opens per operation, closes immediately)

**Fallback Behavior:**
- If DB connection fails, uses `st.session_state.mock_baselines`
- Warning messages displayed but app continues functioning

---

## Custom Components

### 1. Dropdown Component (`dropdown_component.py`)

**Features:**
- Compact spacing design
- Search/filter functionality
- "Select All" / "Deselect All" toggle
- Maintains state across reruns
- Custom border styling (replaces st.divider)

**Parameters:**
- `label` - Display label
- `options` - List of selectable items
- `key` - Unique identifier for state management
- `default_selected` - Initially selected items
- `select_all_text` - Text for toggle button
- `expander_expanded` - Initial expansion state
- `search_placeholder` - Placeholder for search box
- `no_results_text` - Message when search returns nothing
- `none_selected_text` - Message when nothing selected

### 2. Welcome Screen (`popup.py`)

**Features:**
- Fullscreen overlay with branded SVG background
- Responsive "Acessar Painel" button
- Animations (fade-in effects)
- Mobile-friendly (media queries for tablets/phones)
- URL query parameter-based state management

**Technical Details:**
- SVG loaded as base64 encoded string
- Button positioned via Flexbox (bottom-right on desktop, centered on mobile)
- CSS injected via `st.markdown(unsafe_allow_html=True)`
- Uses `st.stop()` to halt execution until dismissed

---

## Performance Optimizations

### Caching Strategy

**Data Loading:**
```python
@st.cache_data
def load_data():
    # Expensive operations cached
    pass
```

Cached functions:
- `buscar_e_processar_dados_completos()` - Smartsheet API calls
- `tratar_macrofluxo()` - Excel file processing
- Main data merge operations

**Cache Invalidation:**
- Automatic on source data changes
- Manual via Streamlit's cache clearing

### Rendering Optimizations

1. **Lazy Loading:** Components rendered only when tab/filter selected
2. **Dynamic Heights:** Gantt chart height = `num_tasks * height_per_task`
3. **Virtual Scrolling:** Large tables use Streamlit's native virtualization
4. **Conditional Rendering:** Sub-stages only rendered when expanded

### Database Optimizations

1. **Connection Management:** Open → Execute → Close immediately
2. **Prepared Statements:** Parameterized queries prevent SQL injection
3. **JSON Storage:** Baseline data stored as JSON for flexible schema
4. **Unique Constraints:** `(empreendimento, version_name)` prevents duplicates

---

## Error Handling

### Import Fallbacks

```python
try:
    from dropdown_component import simple_multiselect_dropdown
except ImportError:
    def simple_multiselect_dropdown(...):
        return st.multiselect(...)  # Fallback to native
```

Similar pattern for:
- Custom components (dropdown, popup, calculate_business_days)
- Data processors (tratamento_dados_reais, tratamento_macrofluxo)

### Data Source Fallbacks

```python
MODO_REAL = True  # Flag set during import attempt

if MODO_REAL:
    # Use real data from Smartsheet/Excel
else:
    # Use mock/example data
```

### Database Fallbacks

```python
if conn:
    # Use MySQL database
else:
    # Use st.session_state.mock_baselines
```

### Graceful Degradation

- Missing data columns → filled with NaN/None
- Invalid dates → `pd.to_datetime(..., errors='coerce')`
- Empty DataFrames → show informative message, don't crash
- API failures → print debug info, use cached/mock data

---

## Development Workflow

### File Organization

```
Main Application Layer (app.py)
   ├── UI Components Layer
   │   ├── dropdown_component.py
   │   └── popup.py
   ├── Data Processing Layer
   │   ├── tratamento_dados_reais.py (Smartsheet)
   │   ├── tratamento_macrofluxo.py (Excel)
   │   └── tratamento_mysql.py (Database)
   └── Utility Layer
       └── calculate_business_days.py
```

### Deployment

**Platform:** Streamlit Cloud (assumed based on secrets usage)

**Configuration:**
1. Upload codebase to GitHub repository
2. Configure secrets in Streamlit Cloud dashboard:
   - `aws_db.host`
   - `aws_db.user`
   - `aws_db.password`
   - `aws_db.database`
3. Deploy from repository

**Local Development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with Smartsheet token
echo "SMARTSHEET_ACCESS_TOKEN=your_token" > .env

# Run application
streamlit run app.py
```

### Testing Strategy

**Manual Testing:**
- Filter combinations
- Baseline creation/switching
- Sub-stage expansion
- Buffer simulation
- Multi-browser compatibility

**Data Validation:**
- Date format consistency
- Business days calculation accuracy
- Variation metrics (VT, VD)
- Completion percentage ranges (0-100)

---

## Browser Compatibility

### Supported Browsers
- Google Chrome (recommended)
- Mozilla Firefox
- Microsoft Edge
- Safari (with minor CSS limitations)

### Responsive Design
- Desktop: Optimized for 1920x1080 and wider
- Tablet: Adjusted layouts via media queries
- Mobile: Simplified views, centered buttons

### JavaScript Requirements
- Essential for Gantt chart interactivity
- Fallback to static views if JS disabled (partial functionality)

---

## Security Considerations

### Sensitive Data Protection

1. **Environment Variables:**
   - Smartsheet token stored in `.env` (not committed to Git)
   - Database credentials in Streamlit secrets (cloud)

2. **SQL Injection Prevention:**
   - Parameterized queries: `cursor.execute(query, (param1, param2))`
   - No user input directly concatenated in SQL

3. **XSS Prevention:**
   - Streamlit automatically escapes user input
   - `unsafe_allow_html=True` only used for trusted static content

4. **.gitignore Recommendations:**
   ```
   .env
   *.csv
   *.xlsx
   __pycache__/
   *.pyc
   .streamlit/secrets.toml
   ```

---

## Known Limitations

1. **Data Freshness:**
   - Cached data requires manual refresh or timeout
   - No real-time synchronization with Smartsheet

2. **Scalability:**
   - Large datasets (>1000 tasks) may impact rendering performance
   - No pagination in Gantt view

3. **Excluded Developments:**
   - Hardcoded exclusions: 'JARDIM DAS HOTÊNSIAS', 'RECANTO DAS OLIVEIRAS'
   - Requires code change to modify exclusions

4. **Browser Limitations:**
   - Heavy reliance on modern JavaScript features
   - Limited offline functionality

5. **Date Handling:**
   - No timezone conversion (assumes local timezone)
   - Holiday calendar may not cover all regions

---

## Future Enhancement Opportunities

### Recommended Features

1. **Real-Time Sync:**
   - WebSocket connection to Smartsheet
   - Auto-refresh when data changes

2. **User Authentication:**
   - Role-based access control
   - User-specific baselines

3. **Export Capabilities:**
   - PDF export of Gantt charts
   - Excel export of filtered data
   - PowerPoint integration

4. **Advanced Analytics:**
   - Predictive completion dates (ML-based)
   - Risk assessment scoring
   - Resource allocation tracking

5. **Mobile App:**
   - Native iOS/Android application
   - Offline mode with sync

6. **Collaboration Features:**
   - Comments on stages
   - Notifications for delays
   - Shared annotations

### Technical Debt

1. **Code Refactoring:**
   - Split `app.py` (6036 lines) into modules
   - Separate concerns (data, UI, business logic)
   - Add type hints throughout

2. **Testing:**
   - Unit tests for utilities
   - Integration tests for data pipeline
   - End-to-end tests for critical flows

3. **Documentation:**
   - Inline code comments
   - API documentation (docstrings)
   - User manual

4. **Dependency Management:**
   - Review and prune unused dependencies
   - Pin versions for reproducibility
   - Regular security updates

---

## Troubleshooting Guide

### Common Issues

#### "Componentes não encontrados"
- **Cause:** Missing custom component files
- **Solution:** Ensure `dropdown_component.py`, `popup.py`, `calculate_business_days.py` exist

#### "Erro de Conexão MySQL"
- **Cause:** Invalid database credentials or network issues
- **Solution:** Verify `st.secrets["aws_db"]` configuration, check firewall

#### "Nenhum dado encontrado para o empreendimento"
- **Cause:** No data for selected development in baseline
- **Solution:** Verify development name matches exactly (case-sensitive)

#### Gantt chart not rendering
- **Cause:** JavaScript errors in browser console
- **Solution:** Check browser console, update browser, clear cache

#### Smartsheet API failures
- **Cause:** Invalid token, rate limiting, network issues
- **Solution:** Verify token in `.env`, check API status, implement retry logic

### Debug Mode

Enable detailed logging:
```python
# In app.py, add at top:
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug prints in critical sections:
print(f"DEBUG: DataFrame shape: {df.shape}")
print(f"DEBUG: Baselines loaded: {len(baselines)}")
```

### Performance Profiling

```python
import time

start = time.time()
# Code to profile
end = time.time()
print(f"Execution time: {end - start:.2f}s")
```

---

## Contact & Support

**Project Owner:** V&M-planejamento  
**License:** MIT License (2025)  
**Repository:** (GitHub URL - if applicable)

For technical issues or feature requests, consult the development team.

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 2.0 | 2025 | Initial baseline.mf.v2 release | V&M-planejamento |

---

## Appendix A: Complete Stage Mappings

### Full Stage Name ↔ Abbreviation Mapping

```python
mapeamento_etapas_usuario = {
    "PROSPECÇÃO": "PROSPEC",
    "LEGALIZAÇÃO PARA VENDA": "LEGVENDA",
    "PULMÃO VENDA": "PULVENDA",
    "PL.LIMP": "PL.LIMP",
    "LEG.LIMP": "LEG.LIMP",
    "ENG. LIMP.": "ENG.LIMP",
    "EXECUÇÃO LIMP.": "EXECLIMP",
    "PL.TER.": "PL.TER",
    "LEG.TER.": "LEG.TER",
    "ENG. TER.": "ENG. TER",
    "EXECUÇÃO TER.": "EXECTER",
    "PL.INFRA": "PL.INFRA",
    "LEG.INFRA": "LEG.INFRA",
    "ENG. INFRA": "ENG.INFRA",
    "EXECUÇÃO INFRA": "EXECINFRA",
    "ENG. PAV": "ENG.PAV",
    "EXECUÇÃO PAV.": "EXEC.PAV",
    "PULMÃO INFRA": "PUL.INFRA",
    "PL.RADIER": "PL.RAD",
    "LEG.RADIER": "LEG.RAD",
    "PULMÃO RADIER": "PUL.RAD",
    "RADIER": "RAD",
    "DEMANDA MÍNIMA": "DEM.MIN",
    "PE. LIMP.": "PE. LIMP.",
    "ORÇ. LIMP.": "ORÇ. LIMP.",
    "SUP. LIMP.": "SUP. LIMP.",
    "PE. TER.": "PE. TER.",
    "ORÇ. TER.": "ORÇ. TER.",
    "SUP. TER.": "SUP. TER.",
    "PE. INFRA": "PE. INFRA",
    "ORÇ. INFRA": "ORÇ. INFRA",
    "SUP. INFRA": "SUP. INFRA",
    "PE. PAV": "PE. PAV",
    "ORÇ. PAV": "ORÇ. PAV",
    "SUP. PAV": "SUP. PAV",
    "PE. ÁREAS COMUNS (ENG)": "PE. ÁREAS COMUNS (ENG)",
    "PE. ÁREAS COMUNS (URB)": "PE. ÁREAS COMUNS (URB)",
    "ORÇ. ÁREAS COMUNS": "ORÇ. ÁREAS COMUNS",
    "SUP. ÁREAS COMUNS": "SUP. ÁREAS COMUNS",
    "EXECUÇÃO ÁREAS COMUNS": "EXECUÇÃO ÁREAS COMUNS"
}
```

---

## Appendix B: Color Reference

### Complete Color Palette

| Sector | Forecast (Light) | Actual (Dark) |
|--------|------------------|---------------|
| PROSPECÇÃO | #FEEFC4 | #AE8141 |
| LEGALIZAÇÃO | #fadbfe | #BF08D3 |
| PULMÃO | #E9E8E8 | #535252 |
| ENGENHARIA | #fbe3cf | #be5900 |
| INFRA | #daebfb | #125287 |
| PRODUÇÃO | #E1DFDF | #252424 |
| ARQUITETURA & URBANISMO | #D4D3F9 | #453ECC |
| VENDA | #dffde1 | #096710 |

### Status Colors

| Status | Color | Hex Code |
|--------|-------|----------|
| Completed On Time | Green | (CSS class) |
| Completed Late | Red | (CSS class) |
| In Progress Behind | Yellow | (CSS class) |
| Default | Black | (CSS class) |
| Today Line | Red | #FF0000 |
| Meta Line | Blue | #0000FF |

---

## Appendix C: Database Queries

### Baseline Creation Query

```sql
INSERT INTO gantt_baselines (empreendimento, version_name, baseline_data, created_date, tipo_visualizacao)
VALUES (%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE 
    baseline_data = VALUES(baseline_data), 
    created_date = VALUES(created_date),
    created_at = CURRENT_TIMESTAMP
```

### Baseline Retrieval Query

```sql
SELECT empreendimento, version_name, baseline_data, created_date, tipo_visualizacao 
FROM gantt_baselines 
ORDER BY created_at DESC
```

### Baseline Deletion Query

```sql
DELETE FROM gantt_baselines 
WHERE empreendimento = %s AND version_name = %s
```

---

**End of AGENTS.md Documentation**
