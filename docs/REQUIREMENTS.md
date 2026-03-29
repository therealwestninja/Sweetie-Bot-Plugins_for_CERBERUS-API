# Requirements

## 1. Functional requirements

### FR-001 Character state
The system shall expose a high-level character state composed of:
- persona profile
- mood
- attention target
- active routine
- speaking state

### FR-002 Persona assets
The system shall load persona definitions from external assets.

### FR-003 Dialogue assets
The system shall load phrase banks and response templates from external assets.

### FR-004 Emote triggering
The system shall support high-level emote triggering without bypassing safety constraints.

### FR-005 Routine triggering
The system shall support named routine triggering, cancellation, and status reporting.

### FR-006 Attention target
The system shall maintain an optional current attention target.

### FR-007 Memory
The system shall support limited, reviewable social memory records.

### FR-008 Web visibility
The web interface shall display character, attention, routine, and dialogue state.

### FR-009 Operator interruption
The operator shall be able to soft-stop or cancel character routines.

### FR-010 Session recording
The system shall support recording operator actions and character events for replay/debugging.

## 2. Non-functional requirements

### NFR-001 Safety precedence
Safety shall override all character behavior.

### NFR-002 Mergeability
The repository structure shall support long-term upstream synchronization.

### NFR-003 Asset separation
Character content shall be editable independently of runtime source code.

### NFR-004 Explainability
High-level events and state changes shall be visible to the operator.

### NFR-005 Recoverability
The system shall define recoverable fallback states for interrupted routines.

### NFR-006 Extensibility
The architecture shall support multiple persona packs over time.

## 3. Constraints
- High-level commands must not directly control raw hardware paths.
- Perception outputs must flow through normalized events/contracts.
- Character routines must remain bounded and interruptible.
- Placeholder code in this scaffold is non-production.
