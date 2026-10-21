# Case 1: Scope Lock Before Implementation

> Regression scenario: input / expected behaviors pair

## Input
```
/freeze — only touch the src/auth/ directory. Don't touch anything else.
```

## Expected Key Behaviors
- Parses the request from the message alone (no project files need to be read)
- Declares a FROZEN SCOPE block: EDITABLE = `src/auth/**`, FROZEN = everything else
- Outputs the block and then STOPS (no further implementation)
- Does NOT start implementing anything after the declaration

## Should NOT
- Immediately start editing files after declaring scope
- Assume "don't touch the rest" means only the current file
- Skip the declaration and jump to implementation
- Expand the editable zone based on "it would be easier"
