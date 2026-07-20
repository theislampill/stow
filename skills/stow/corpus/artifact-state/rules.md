# Artifact and state contracts

A STOW-native rule for revising an existing artifact or state record safely. It applies when the response changes an artifact that already exists. It activates on artifact-revision turns and is reviewed, not mechanically enforced.

## STOW-ART-001

Do not overwrite an artifact whose current content you have not read. Ground a revision in the artifact's present state and keep unrelated content.

Read the current content first. Apply the bounded change the task asks for. Keep unrelated and concurrent content unless the contract explicitly replaces it. When the contract is a full replacement, that replacement is the task, and this rule governs partial revision rather than a contracted full rewrite. This rule governs the artifact you produce, not any tool permission.

**Conforming:** I read the current state file, applied the one field update, and kept the other entries.

**Non-conforming:** Replacing the state file from an old copy without reading the current version.
