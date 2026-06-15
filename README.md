# FitFindr

A multi-tool AI agent that helps users find secondhand clothing and style it.

## Tool Inventory

**search_listings(description: str, size: str|None, max_price: float|None) → list[dict]**
Searches mock listings by keyword relevance, size, and price. Returns ranked list of 
matching listing dicts, or empty list if nothing matches.

- **Retry logic**: if search_listings returns no results, the agent automatically 
  retries with no size filter and 4x the price limit, and informs the user what 
  was adjusted.
**suggest_outfit(new_item: dict, wardrobe: dict) → str**
Calls the LLM to suggest 1-2 outfit combinations using the new item and the user's 
wardrobe pieces. If wardrobe is empty, returns general styling advice instead.

**create_fit_card(outfit: str, new_item: dict) → str**
Calls the LLM to generate a casual Instagram-style caption for the outfit. If outfit 
is empty, returns an error string without crashing.

## How the Planning Loop Works

1. Parse the user's natural language query using the LLM to extract description, 
   size, and max_price.
2. Call search_listings() with those parameters.
3. If results are empty, set session["error"] and return immediately — 
   suggest_outfit and create_fit_card are never called.
4. If results found, set selected_item = results[0].
5. Call suggest_outfit(selected_item, wardrobe).
6. Call create_fit_card(outfit_suggestion, selected_item).
7. Return session.

The agent's behavior changes based on what search_listings returns — it does not 
call all three tools unconditionally.

## State Management

All state lives in a session dict initialized at the start of each interaction. 
Fields: query, parsed, search_results, selected_item, wardrobe, outfit_suggestion, 
fit_card, error. Each tool receives only the specific value it needs from the session — 
no tool ever receives the raw query string directly.

## Error Handling

- **search_listings**: returns [] on no match → agent sets session["error"] and 
  returns early. User sees: "No listings found for your search. Try a broader 
  description, different size, or higher price limit."
- **suggest_outfit**: if wardrobe["items"] is empty → LLM gives general styling 
  advice instead of specific combinations. No crash.
- **create_fit_card**: if outfit string is empty → returns "Unable to generate 
  fit card: no outfit suggestion provided." No crash.

Example triggered: running `create_fit_card('', item)` returns the error string 
rather than raising an exception.

## Spec Reflection

The planning.md spec helped by forcing the conditional logic to be written out 
before coding — the early-exit branch on empty search results was clear from the 
spec and translated directly into code.

One divergence: the spec didn't anticipate that PowerShell requires a different 
venv activation command than Mac/Linux. Setup required an extra execution policy 
step on Windows.

## AI Usage

## AI Usage

1. For search_listings, I provided the Tool 1 spec block from planning.md and
   asked Claude to implement the function using load_listings(). I verified it
   handled the empty-results case and price filter before running it. I revised
   the scoring logic to search across title, description, and style_tags rather
   than title only, which the initial version missed.

2. For run_agent(), I provided the Architecture diagram and Planning Loop section
   from planning.md and asked Claude to implement the function. I verified the
   generated code branched on search_listings results. I overrode the initial
   file structure — the first version placed imports in the wrong order, breaking
   the file, so I reorganized agent.py into a clean single structure.