# FitFindr — planning.md

FitFindr takes a user's natural language query and extracts a description, size, and price limit to search mock secondhand listings. If a match is found, it passes the top result and the user's wardrobe to an LLM to suggest outfit combinations, then generates shareable caption content. If no listings match, the agent stops and does not call the remaining tools.
---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock listings dataset for items matching the user's description, size, and price limit. Returns a ranked list of matches sorted by relevance.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- description (str): keywords describing the item the user wants
- size (str | None): size to filter by, or None to skip size filtering
- max_price (float | None): maximum price inclusive, or None to skip price filtering

**What it returns:**
A list of listing dicts sorted by relevance score. Each dict contains: id, title, description, category, style_tags, size, condition, price, colors, brand, and platform. Returns an empty list [] if nothing matches.
**What happens if it fails or returns nothing:**

<!-- What should the agent do if no listings match? -->
Agent sets session["error"] to "No listings found for your search. Try a broader description, different size, or higher price limit." and returns the session early without calling suggest_outfit or create_fit_card.

### Tool 2: suggest_outfit

**What it does:**
Given a thrifted item and the user's existing wardrobe, calls the LLM to suggest 1-2 complete outfit combinations using pieces the user already owns.

**Input parameters:**
- new_item (dict): a listing dict for the item the user is considering buying
- wardrobe (dict): a dict with an items key containing a list of wardrobe item dicts, may be empty

**What it returns:**
A non-empty string describing 1-2 outfit suggestions with specific wardrobe pieces named.


**What happens if it fails or returns nothing:**
If wardrobe['items'] is empty, call the LLM for general styling advice instead of specific combinations.

---

### Tool 3: create_fit_card

**What it does:**
Generates a 2-4 sentence shareable Instagram-style caption for the outfit, mentioning the item name, price, and platform naturally.

**Input parameters:**
- outfit (str): the outfit suggestion string from suggest_outfit
- new_item (dict): the listing dict for the thrifted item.

**What it returns:**
A casual, authentic caption string that sounds like a real OOTD post.

**What happens if it fails or returns nothing:**
If outfit is empty or whitespace, returns the string "Unable to generate fit card: no outfit suggestion provided." without crashing.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
1. Parse the user's query using the LLM to extract description (str), 
   size (str or None), and max_price (float or None). Store in session["parsed"].

2. Call search_listings(description, size, max_price).
   Store results in session["search_results"].
   If results == []: set session["error"] = "No listings found for your search. 
   Try a broader description, different size, or higher price limit." and return 
   session immediately.

3. Set session["selected_item"] = session["search_results"][0].

4. Call suggest_outfit(session["selected_item"], session["wardrobe"]).
   Store result in session["outfit_suggestion"].

5. Call create_fit_card(session["outfit_suggestion"], session["selected_item"]).
   Store result in session["fit_card"].

6. Return session.

---

## State Management

All state is stored in a session dict initialized by _new_session(). 
The dict tracks: query (original input), parsed (extracted description/size/price), 
search_results (list from search_listings), selected_item (results[0], passed to 
suggest_outfit), wardrobe (passed in at start), outfit_suggestion (string from 
suggest_outfit, passed to create_fit_card), fit_card (final output string), 
and error (set on early termination). No tool receives raw query text — each 
tool receives only the specific value it needs from the session.

---

## Error Handling

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Set session["error"], return early, skip remaining tools |
| suggest_outfit | Wardrobe is empty | Call LLM for general styling advice instead of specific combinations |
| create_fit_card | Outfit input is missing or empty | Return error string "Unable to generate fit card: no outfit suggestion provided." |

---

## Architecture

User query
    │
    ▼
Planning Loop
    │
    ├─► Parse query → extract description, size, max_price
    │       │
    │       ▼
    ├─► search_listings(description, size, max_price)
    │       │
    │       ├── results == [] ──► set session["error"] ──► return session (STOP)
    │       │
    │       └── results found ──► session["selected_item"] = results[0]
    │                                       │
    ├─► suggest_outfit(selected_item, wardrobe)
    │       │
    │       ├── wardrobe empty ──► LLM gives general styling advice
    │       │
    │       └── wardrobe has items ──► LLM suggests specific combinations
    │                                       │
    │                               session["outfit_suggestion"] = result
    │                                       │
    └─► create_fit_card(outfit_suggestion, selected_item)
            │
            └── session["fit_card"] = result
                    │
                    ▼
                Return session

---

## AI Tool Plan

Milestone 3 — Individual tool implementations:
I'll use Claude. For each tool I'll paste that tool's spec block from planning.md 
(inputs, return value, failure mode) and ask it to implement that one function. 
I'll verify each generated function handles the failure mode before running it, 
then test with at least 2 inputs.

Milestone 4 — Planning loop and state management:
I'll give Claude the Architecture diagram and Planning Loop section from planning.md 
and ask it to implement run_agent(). I'll verify the generated code branches on 
search_listings results and doesn't call all tools unconditionally.

---

## A Complete Interaction (Step by Step)
Example query: "I'm looking for a vintage graphic tee under $30. 
I mostly wear baggy jeans and chunky sneakers."

Step 1: Parse query → description="vintage graphic tee", size=None, max_price=30.0

Step 2: search_listings("vintage graphic tee", size=None, max_price=30.0)
        Returns: [{"title": "Y2K Baby Tee", "price": 18.0, "platform": "depop", ...}, ...]
        session["selected_item"] = results[0]

Step 3: suggest_outfit(selected_item, wardrobe)
        Wardrobe has items → LLM suggests:
        "Pair this Y2K baby tee with your baggy dark wash jeans and chunky 
        white sneakers for a 90s-inspired street look."
        session["outfit_suggestion"] = above string

Step 4: create_fit_card(outfit_suggestion, selected_item)
        Returns: "thrifted this y2k butterfly tee off depop for $18 and it 
        goes so hard with my baggy jeans 🦋 full fit in my stories"
        session["fit_card"] = above string

Final output: user sees the fit card caption.

Error path: If step 2 returns [] → session["error"] is set, steps 3 and 4 
are skipped, user sees the error message instead.
