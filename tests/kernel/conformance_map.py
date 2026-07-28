"""Machine-readable slice mapping; structural coverage is not full conformance."""
SCENARIO_MAP = {
  1:"CMD-001",2:"CMD-001",3:"LIF-001",4:"EVT-004",5:"CMD-014",6:"CMD-014",7:"AUD-001",8:"RPL-003",
  9:"CMD-014",10:"POR-008",11:"ADV-015",12:"CMD-001",13:"CMD-001",14:"ADV-009",15:"ADV-009",16:"AUD-009",
  17:"CMD-004",18:"CMD-004",19:"CMD-004",20:"CMD-004",21:"CMD-004",22:"CMD-004",23:"WRT-003",24:"WRT-005",
  25:"WRT-006",26:"AUD-009",27:"AUD-006",28:"AUT-008",29:"AUT-002",30:"AUT-003",31:"AUT-005",32:"AUT-007",
  33:"AUT-010",34:"AUT-011",35:"AUT-008",36:"APR-008",37:"APR-005",38:"APR-002",39:"APR-004",40:"APR-008",
  41:"RES-003",42:"RES-002",43:"APR-001",44:"ADV-001",45:"ADV-001",46:"RES-003",47:"LIF-001",48:"LIF-002",
  49:"CMD-007",50:"CMD-002",51:"EVT-003",52:"CMD-008",53:"CMD-008",54:"APR-001",55:"RES-002",56:"CMD-012",
  57:"CMD-008",58:"CMD-008",59:"ADV-002",60:"EVT-003",61:"EVT-003",62:"ADV-001",63:"ADV-001",64:"ADV-001",
  65:"ADV-001",66:"ADV-002",67:"ADV-002",68:"ADV-002",69:"ADV-002",70:"RPL-003",71:"RPL-004",72:"EVT-002",
  73:"AUD-009",74:"RPL-005",75:"RPL-005",76:"CMD-003",77:"CMD-003",78:"CMD-002",79:"WRT-006",80:"TOL-002",
}

# Constitutional bootstrap runtime coverage; this remains slice evidence rather
# than a claim of full kernel conformance.
BOOTSTRAP_SCENARIO_MAP = {
  "valid_genesis": ("BST-001", "BST-003", "BST-004", "BST-011", "BST-012"),
  "atomic_append": ("BST-001", "BST-002", "BST-004"),
  "ordinary_work_excluded": ("BST-005",),
  "exact_redelivery": ("BST-006",),
  "competing_genesis": ("BST-007",),
  "human_owner_and_decider": ("BST-008", "BST-011"),
  "genesis_authority_contained": ("BST-010",),
  "reserved_types": ("BST-012",),
  "replay": ("RPL-003", "RPL-005"),
}

# Ordinary draft Role creation coverage. This is focused slice evidence, not a
# claim that the complete 260-scenario kernel conformance catalog is satisfied.
CREATE_ROLE_SCENARIO_MAP = {
  "draft_creation": ("CMD-001", "LIF-013"),
  "active_creation_prohibited": ("LIF-014",),
  "founding_role_distinct": ("LIF-015", "BST-001"),
  "organization_stream": ("EVT-011", "EVT-012"),
  "projection_replay": ("EVT-013", "RPL-003", "RPL-005"),
  "organization_concurrency": ("EVT-003", "EVT-014"),
  "organization_isolation": ("CMD-004", "CMD-015"),
  "authority_fail_closed": ("AUT-008", "ADV-011"),
  "idempotency": ("CMD-008", "CMD-012"),
}
