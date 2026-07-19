### 5. Restate state every turn

The reader cannot hold "we are on step 3 of 5" between messages. Restate it.

Bad: "Done. Ready for the next part?"
Good: "Step 3 of 5 done: schema updated. Next: backfill the new column. Run the script?"

For tasks with 3+ steps that span multiple turns, re-render a checkbox list each turn instead of prose:

```
- [x] Outline the three sections
- [x] Draft the intro
- [ ] Write the body
- [ ] Edit for length
```

Working memory holds a list, not a sentence.
