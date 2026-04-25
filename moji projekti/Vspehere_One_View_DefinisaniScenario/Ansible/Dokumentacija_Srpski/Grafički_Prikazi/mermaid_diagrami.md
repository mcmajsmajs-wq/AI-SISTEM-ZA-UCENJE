# Mermaid Dijagrami - Ansible Automation

## 📋 Sadržaj

1. [Glavni Orchestrator Flow](#glavni-orchestrator-flow)
2. [Daily Scan Workflow](#daily-scan-workflow)
3. [VMware Patching Phases](#vmware-patching-phases)
4. [OneView Update Process](#oneview-update-process)
5. [Combined Workflow](#combined-workflow)
6. [Error Handling Flow](#error-handling-flow)

---

## 🎯 Glavni Orchestrator Flow

```mermaid
graph TD
    A[🚀 Start: main.yml] --> B{📋 Action Parameter}
    B -->|daily-scan| C[📊 daily-scan.yml]
    B -->|scenario1| D[🔧 scenario1-vmware-patching.yml]
    B -->|scenario2| E[🔄 scenario2-oneview-update.yml]
    B -->|scenario3| F[🔀 scenario3-combined.yml]
    B -->|scenario4| G[🏗️ scenario4-cluster-patching.yml]
    B -->|full-workflow| H[🎯 full-workflow.yml]
    
    C --> C1[🔍 VMware Scan]
    C --> C2[🖥️ OneView Scan]
    C --> C3[📈 Analysis]
    C --> C4[📄 Reports]
    
    D --> D1[✅ Pre-Checks]
    D --> D2[🔄 Lifecycle Manager]
    D --> D3[✔️ Compliance Check]
    D --> D4[📦 Staging]
    D --> D5[🔨 Remediation]
    D --> D6[🔍 Post-Verification]
    
    E --> E1[🔐 Authentication]
    E --> E2[💾 Firmware Repository]
    E --> E3[📝 Template Update]
    E --> E4[🚀 Update from Template]
    E --> E5[✅ Post-Update Verification]
    
    F --> F1[🔀 Combined Operations]
    G --> G1[🏗️ Cluster Operations]
    H --> H1[🎯 Full Workflow]
    
    C4 --> Z[✅ End]
    D6 --> Z
    E5 --> Z
    F1 --> Z
    G1 --> Z
    H1 --> Z
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#fce4ec
    style F fill:#f3e5f5
    style G fill:#e0f2f1
    style H fill:#fff8e1
    style Z fill:#e8f5e8
```

---

## 📊 Daily Scan Workflow

```mermaid
graph LR
    A[🚀 Start Daily Scan] --> B[📝 Initialize Logging]
    B --> C[📁 Create Report Directory]
    C --> D[🔍 Check vCenter Access]
    D --> E[🔍 Check OneView Access]
    E --> F[🖥️ VMware Scanning]
    F --> G[💻 OneView Scanning]
    G --> H[📈 Compare with Previous Day]
    H --> I[📊 Generate Reports]
    I --> J[📄 JSON Report]
    I --> K[🌐 HTML Report]
    J --> L[✅ End]
    K --> L
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#fce4ec
    style F fill:#e3f2fd
    style G fill:#f1f8e9
    style H fill:#fff8e1
    style I fill:#e0f2f1
    style J fill:#e8f5e8
    style K fill:#e8f5e8
    style L fill:#e8f5e8
```

### Daily Scan - Detaljna Faza

```mermaid
graph TD
    A[🚀 Daily Scan Start] --> B[📝 Phase 1: Initialization]
    B --> C[📁 Create Directories]
    C --> D[🔍 Phase 2: Access Checks]
    D --> E[🖥️ vCenter Connection]
    D --> F[💻 OneView Authentication]
    E --> G[📊 Phase 3: VMware Scanning]
    F --> G
    G --> H[📋 VM Info Collection]
    G --> I[🖥️ Host Facts Collection]
    G --> J[💾 Datastore Info]
    G --> K[🏗️ Cluster Info]
    G --> L[🚨 Alarm Collection]
    H --> M[💻 Phase 4: OneView Scanning]
    I --> M
    J --> M
    K --> M
    L --> M
    M --> N[🏢 Appliance Status]
    M --> O[📦 Enclosures]
    M --> P[🖥️ Server Hardware]
    M --> Q[🔌 Logical Interconnects]
    M --> R[📝 Server Profiles]
    N --> S[📈 Phase 5: Analysis]
    O --> S
    P --> S
    Q --> S
    R --> S
    S --> T[📊 Compare with Previous Day]
    T --> U[📄 Phase 6: Reporting]
    U --> V[📋 JSON Report]
    U --> W[🌐 HTML Report]
    V --> X[✅ End]
    W --> X
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#e3f2fd
    style F fill:#f1f8e9
    style G fill:#fff8e1
    style H fill:#e0f2f1
    style I fill:#fce4ec
    style J fill:#f3e5f5
    style K fill:#e8f5e8
    style L fill:#fff3e0
    style M fill:#fff8e1
    style N fill:#e1f5fe
    style O fill:#e8f5e8
    style P fill:#fce4ec
    style Q fill:#f3e5f5
    style R fill:#fff3e0
    style S fill:#fff8e1
    style T fill:#e0f2f1
    style U fill:#e8f5e8
    style V fill:#e8f5e8
    style W fill:#e8f5e8
    style X fill:#e8f5e8
```

---

## 🔧 VMware Patching Phases

```mermaid
graph TD
    A[🚀 Start VMware Patching] --> B[✅ Phase 1: Pre-Checks]
    B --> C{🔍 Backup Check}
    C -->|❌ No Backup| Z[🛑 STOP - No Backup]
    C -->|✅ Backup OK| D[🔄 Phase 2: Lifecycle Manager]
    D --> E[🔄 Sync Updates]
    E --> F[📎 Attach Baseline]
    F --> G[✔️ Phase 3: Compliance Check]
    G --> H{✅ Compliant?}
    H -->|✅ Yes| I[⏭️ SKIP - Already Compliant]
    H -->|❌ No| J[📦 Phase 4: Staging]
    J --> K[📋 Pre-Remediation Check]
    K --> L[📥 Copy Patch Files]
    L --> M[🔍 Phase 5: Remediation]
    M --> N[🔍 Final Backup Check]
    N --> O[🔧 Enter Maintenance Mode]
    O --> P[🔨 Apply Patches]
    P --> Q[⏱️ Wait for Restart]
    Q --> R[🔓 Exit Maintenance Mode]
    R --> S[🔍 Phase 6: Post-Verification]
    S --> T[✔️ Compliance Recheck]
    T --> U[🏗️ Build Verification]
    U --> V[🔄 VMotion Test]
    V --> W[✅ End]
    I --> W
    Z --> X[❌ Failed]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#ffebee
    style D fill:#e8f5e8
    style E fill:#e8f5e8
    style F fill:#e8f5e8
    style G fill:#fff3e0
    style H fill:#ffebee
    style I fill:#fff8e1
    style J fill:#f3e5f5
    style K fill:#fff3e0
    style L fill:#e8f5e8
    style M fill:#fff8e1
    style N fill:#ffebee
    style O fill:#fff3e0
    style P fill:#e8f5e8
    style Q fill:#fff8e1
    style R fill:#e8f5e8
    style S fill:#fff3e0
    style T fill:#e8f5e8
    style U fill:#e8f5e8
    style V fill:#e8f5e8
    style W fill:#e8f5e8
    style X fill:#ffebee
```

---

## 🔄 OneView Update Process

```mermaid
graph TD
    A[🚀 Start OneView Update] --> B[🔐 Phase 1: Authentication]
    B --> C[🔍 Check Server Profiles]
    C --> D[🔧 Check Maintenance Mode]
    D --> E[💾 Phase 2: Firmware Repository]
    E --> F[🔍 Check Available SPP]
    F --> G[✅ Verify Target Version]
    G --> H[📝 Phase 3: Template Update]
    H --> I[🔍 Find Template]
    I --> J[🔄 Update Firmware Baseline]
    J --> K[🚀 Phase 4: Update from Template]
    K --> L[✅ Consistency Check]
    L --> M[🔄 Start Update Process]
    M --> N[⏱️ Monitor Progress<br/>15-30 minutes]
    N --> O[🔍 Phase 5: Post-Update Verification]
    O --> P[✅ Verify Firmware Version]
    P --> Q[🖥️ Check Server Status]
    Q --> R[✅ End]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#f3e5f5
    style F fill:#fff3e0
    style G fill:#e8f5e8
    style H fill:#fff8e1
    style I fill:#fff3e0
    style J fill:#e8f5e8
    style K fill:#e0f2f1
    style L fill:#e8f5e8
    style M fill:#e8f5e8
    style N fill:#fff8e1
    style O fill:#fff3e0
    style P fill:#e8f5e8
    style Q fill:#e8f5e8
    style R fill:#e8f5e8
```

---

## 🔀 Combined Workflow (Scenario 3)

```mermaid
graph TD
    A[🚀 Start Combined Workflow] --> B[📋 Initialize Combined Process]
    B --> C[🔍 Pre-Checks for Both Systems]
    C --> D[✅ VMware Backup Check]
    C --> E[✅ OneView Status Check]
    D --> F{✅ Both OK?}
    E --> F
    F -->|❌ No| Z[🛑 STOP - Pre-check Failed]
    F -->|✅ Yes| G[🔄 VMware Patching Process]
    G --> H[✅ VMware Completion Check]
    H --> I[🔄 OneView Update Process]
    I --> J[✅ OneView Completion Check]
    J --> K[📊 Combined Verification]
    K --> L[📄 Combined Report]
    L --> M[✅ End]
    Z --> N[❌ Failed]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e3f2fd
    style E fill:#f1f8e9
    style F fill:#ffebee
    style G fill:#e8f5e8
    style H fill:#fff3e0
    style I fill:#fce4ec
    style J fill:#fff3e0
    style K fill:#fff8e1
    style L fill:#e0f2f1
    style M fill:#e8f5e8
    style N fill:#ffebee
```

---

## 🏗️ Cluster Patching Workflow (Scenario 4)

```mermaid
graph TD
    A[🚀 Start Cluster Patching] --> B[📋 Initialize Cluster Process]
    B --> C[🔍 Get Cluster Hosts]
    C --> D[🔄 Iterate Through Hosts]
    D --> E[🖥️ Select Next Host]
    E --> F[✅ Host Pre-Checks]
    F --> G{✅ Host Ready?}
    G -->|❌ No| H[⏭️ Skip Host]
    G -->|✅ Yes| I[🔄 Apply Scenario 3 to Host]
    I --> J[✅ Host Completion Check]
    J --> K{📋 More Hosts?}
    K -->|✅ Yes| E
    K -->|❌ No| L[📊 Cluster Verification]
    H --> K
    L --> M[📄 Cluster Report]
    M --> N[✅ End]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#fff3e0
    style F fill:#fff8e1
    style G fill:#ffebee
    style H fill:#fff8e1
    style I fill:#e0f2f1
    style J fill:#e8f5e8
    style K fill:#ffebee
    style L fill:#fff3e0
    style M fill:#e0f2f1
    style N fill:#e8f5e8
```

---

## 🚨 Error Handling Flow

```mermaid
graph TD
    A[🚀 Start Any Operation] --> B[🔍 Try Operation]
    B --> C{✅ Success?}
    C -->|✅ Yes| D[📝 Log Success]
    C -->|❌ No| E[🚨 Log Error]
    E --> F[🔍 Analyze Error Type]
    F --> G{🔍 Connection Error?}
    G -->|✅ Yes| H[🔄 Retry Connection]
    H --> I{⏱️ Max Retries?}
    I -->|❌ No| B
    I -->|✅ Yes| J[🛑 Stop - Connection Failed]
    G -->|❌ No| K{🔍 Backup Error?}
    K -->|✅ Yes| L[🛑 Stop - Backup Required]
    K -->|❌ No| M{🔍 Resource Error?}
    M -->|✅ Yes| N[⏸️ Pause - Wait for Resources]
    N --> O[⏱️ Wait 5 minutes]
    O --> B
    M -->|❌ No| P[🛑 Stop - Unknown Error]
    D --> Q[✅ Continue Next Step]
    J --> R[❌ End - Failed]
    L --> R
    P --> R
    N --> S[🔄 Retry Operation]
    S --> B
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#ffebee
    style D fill:#e8f5e8
    style E fill:#ffebee
    style F fill:#fff3e0
    style G fill:#ffebee
    style H fill:#fff8e1
    style I fill:#ffebee
    style J fill:#ffebee
    style K fill:#ffebee
    style L fill:#ffebee
    style M fill:#ffebee
    style N fill:#fff8e1
    style O fill:#fff8e1
    style P fill:#ffebee
    style Q fill:#e8f5e8
    style R fill:#ffebee
    style S fill:#fff8e1
```

---

## 📊 Execution Modes Flow

```mermaid
graph TD
    A[🚀 Start Operation] --> B{🎯 Execution Mode}
    B -->|🔍 simulate| C[📝 Log What Would Happen]
    B -->|🧪 test| D[✅ Verify All Pre-conditions]
    B -->|🏭 production| E[🔨 Execute Real Changes]
    
    C --> F[📄 Generate Simulation Report]
    D --> G[✅ Generate Test Report]
    E --> H[🔍 Verify Production Ready]
    H --> I{✅ All Checks Pass?}
    I -->|❌ No| J[🛑 Stop - Not Ready]
    I -->|✅ Yes| K[🔨 Execute Changes]
    K --> L[📊 Generate Production Report]
    
    F --> M[✅ End - Simulated]
    G --> N[✅ End - Tested]
    L --> O[✅ End - Executed]
    J --> P[❌ End - Failed]
    
    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#e3f2fd
    style D fill:#fff8e1
    style E fill:#ffebee
    style F fill:#e3f2fd
    style G fill:#fff8e1
    style H fill:#fff3e0
    style I fill:#ffebee
    style J fill:#ffebee
    style K fill:#e8f5e8
    style L fill:#e8f5e8
    style M fill:#e3f2fd
    style N fill:#fff8e1
    style O fill:#e8f5e8
    style P fill:#ffebee
```

---

## 📝 Korišćenje Mermaid Dijagrama

Ovi dijagrami se mogu koristiti u:

1. **Markdown dokumentima** - Većina modernih Markdown editora podržava Mermaid
2. **GitHub/GitLab** - Automatski renderuju Mermaid dijagrame
3. **VS Code** - Sa Mermaid preview ekstenzijom
4. **Online alatima** - mermaid.live, mermaid-js.github.io
5. **Dokumentacionim sistemima** - Confluence, Notion, itd.

### Primer uključivanja u Markdown:

```markdown
```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```
```

---

**Verzija:** 1.0  
**Autor:** Ansible Automation Team  
**Datum:** 2024-02-07  
**Jezik:** Srpski (Cirilica)