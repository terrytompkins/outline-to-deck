# Prompts for each stage

There are two ways to run a presentation through this project:

- **Guided mode:** Claude walks you through every step with questions and tells you when to start a new chat. You need only the two prompts in the next section.
- **Manual mode:** you run each step yourself with the numbered prompts below, when you want control over each step. Claude does exactly the step you ask for, then stops.

If your first message doesn't name a mode, Claude uses the mode in BRIEF.md, or asks. Either way, Claude won't start the deck until you've approved the outline.

**The tools bundle.** Attach `deck-tools.zip` to the chat for prompts 6–9 (Phase 2). Attaching it in Phase 1 chats lets Claude lint the outline too.

## Guided mode

### Start
> Use guided mode. Take me from my idea to a finished deck.

### Resume, in any new chat
> Continue my deck.

Claude reads the project files, tells you where things stand, and picks up from there.

## Manual mode

Start each prompt in a **fresh chat** in the project unless it says otherwise. The project files carry the state between chats. "Continue my deck" works here too: Claude names the next step and does only that one.

### 1. Kickoff: fill in the brief
> Read BRIEF.md. Interview me to fill in every `[TBD: …]` field, a few questions at a time. When we're done, write BRIEF.md to the project and summarize it in five lines. Then stop; don't start the outline.

### 2. First outline
> Following the project instructions, research the topic in BRIEF.md and write outline v0.1. Map the coverage dimensions before choosing a structure. Include the time plan, origin tags, Coverage gaps, and source reconciliation. Add callouts, slide types, layouts and diagrams where they genuinely fit, following TAGS.md, LAYOUTS.md and the style guide, and list what you added. Lint the outline if the tools are attached. Write OUTLINE.md and DECISIONS.md to the project when done.

### 3. Revise (same chat is fine for small changes)
> Revise sections [N, N.M]: [what to change]. Don't renumber anything. Bump the version, record the change under "Changes by version", and write the files at the end.

### 4. Independent review before approval
> Review OUTLINE.md against BRIEF.md, DECISIONS.md, TAGS.md, LAYOUTS.md and the project instructions. Lint it if the tools are attached. Don't restructure or renumber. Give me a gap list ranked by value to attendees, check that tags and layouts follow their proposal rules and limits, and flag any claim that needs an "As of" date or an [UNVERIFIED] tag. Propose changes; don't write the files until I approve them. When I approve, apply exactly the approved changes and mark the outline as reviewed.

### 5. Approve
> I approve outline v[X.Y]. Record the gate entry "- [today's date] · Decided · Outline v[X.Y] approved; Phase 2 begins." in DECISIONS.md, update OUTLINE.md's status, and write both files.

### 6. Start Phase 2 (fresh chat, attach deck-tools.zip)
> Start Phase 2. DECISIONS.md records approval of outline v[X.Y]; build from it as written, without re-researching or revising content. Follow DECK-BUILD-SPEC.md with the attached tools and the style in BRIEF.md. Before writing slides, lint the outline, confirm the pinned library versions, and list anything you can't render as specified. Pass 1: title, agenda, and every horizontal slide. Check it, write OUTPUT-NOTES.md, then stop and send me the file.

### 7. Phase 2, pass 2
> Continue with pass 2: vertical slides in priority order, Core sections first. Send an interim file after the Core sections, then finish Brief and Self-guided. Run every check in DECK-BUILD-SPEC.md, report the results as numbers, and write OUTPUT-NOTES.md.

### 8. Change content after the build (attach the deck and deck-tools.zip)
> Change [section N.M]: [what]. Update OUTLINE.md first (bump the version and record a Decided entry), then rebuild only the affected topic, re-run the checks, update OUTPUT-NOTES.md, and send the updated deck.

### 9. Switch styles (attach deck-tools.zip)
> I've uploaded [STYLE-X.md]. Make it the active style in BRIEF.md, lint the outline for anything the new style renders more simply, tell me what you find, and rebuild the deck with the new style.

### Recovery: a chat lost its file tools
> A previous chat in this project produced changes it couldn't write to the files. Use past-chat search to find the message containing "Updates for OUTLINE.md" from [approximate date]. Read it in full, apply exactly those changes to the current files, write them, and list by section number what you applied and anything you couldn't.
