# Case 1: Scope Lock Before Implementation

> Skills-Coach test scenario — input/expected_behaviors pair

## Input
```
/freeze — only touch the src/auth/ directory. Don't touch anything else.
```

## Expected Key Behaviors
- Reads CLAUDE.md / open files to establish context (Read-only phase)
- Declares FROZEN ZONE: all paths NOT matching `src/auth/**`
- Declares EDITABLE ZONE: `src/auth/**` only
- Outputs a clear zone declaration and then STOPS (no further implementation)
- Does NOT start implementing anything after the declaration

## Should NOT
- Immediately start editing files after declaring scope
- Assume "don't touch the rest" means only the current file
- Skip zone declaration and jump to implementation
- Expand the editable zone based on "it would be easier"
