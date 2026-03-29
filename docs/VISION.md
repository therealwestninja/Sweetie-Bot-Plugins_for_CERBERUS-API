# Vision Document

## Working title
**Sweetie-Bot Fork**

## Vision statement
Build a character-robot system that can transform a capable quadruped robotics stack into a believable, expressive, safe, and operator-friendly fictional companion platform.

The first public target is not a fully autonomous companion.
The first public target is a **polished convention/performance build** that can:
- greet
- emote
- speak in-character
- perform short routines
- react socially
- remain safe and interruptible

## Product vision
Sweetie-Bot should feel like:
- a distinct character
- responsive to attention and praise
- staged and charming rather than chaotic
- expressive enough to read from across a room
- safe enough that the operator always retains control

## Anti-vision
This project is **not** trying, at first, to be:
- an unrestricted embodied LLM
- a free-roaming home robot
- a raw direct-control experiment with no operator layer
- a rewrite of the upstream robotics/control stack
- a replacement for hardware safety logic

## Experience pillars

### 1. Character coherence
Voice, motion, timing, and display language must feel like one entity.

### 2. Safe expressiveness
Every cute or theatrical behavior must remain bounded by safety, stability, and crowd awareness.

### 3. Operator confidence
A human operator should always understand:
- what the robot is trying to do
- why it is doing it
- what to interrupt
- how to recover

### 4. Content-first iteration
Persona, dialogue, routines, and emotes should be editable as assets without recompiling core logic.

### 5. Convention-first deployment
The shortest path to a memorable public experience is the first success criterion.

## Phase vision

### Phase 1: Character shell
The robot visibly behaves like a character.

### Phase 2: Talking performer
The robot speaks, emotes, and executes short routines.

### Phase 3: Social performer
The robot orients to people, reacts to simple attention cues, and performs in a more socially legible way.

### Phase 4: Companion beta
The robot supports constrained memory, preferences, and repeat interactions.

## Success indicators
- users can identify distinct moods without explanation
- speech and motion feel synchronized rather than accidental
- the operator can run a short demo repeatedly with low failure rate
- character assets can be updated without invasive runtime changes
- safe fallback behavior is obvious and reliable

## Long-term aspiration
A reusable character-robot framework that can support other personas beyond Sweetie-Bot without rebuilding the entire stack.
