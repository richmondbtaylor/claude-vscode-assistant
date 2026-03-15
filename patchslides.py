
f = "C:/Users/richm/.claude/2026-03-13 promptAnything.io - Keynote Pitch Deck.html"
h = open(f, encoding="utf-8").read()

# S4: replace 5-circle right side with Before/After
marker4 = "Steps to a<br>deploy-ready prompt"
if marker4 in h:
    start = h.rfind("<div style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:0.8rem;"", 0, h.find(marker4))
    end = h.find("</div></div></div>", h.find(marker4)) + len("</div></div></div>")
    new4 = (
        "<div style=\"display:flex;flex-direction:column;gap:0.55rem;width:100%;\">"
        "<div style=\"background:var(--dk);border-radius:6px;padding:0.8rem 1rem;border-left:3px solid #E05252;\">"
        "<div style=\"font-size:0.55rem;font-weight:700;text-transform:uppercase;color:#E05252;margin-bottom:0.3rem;\">Before</div>"
        "<p style=\"font-size:0.72rem;\">Trial-and-error prompts. Rewrites. Abandoned ideas. Hours lost on guesswork.</p></div>"
        "<div style=\"text-align:center;color:var(--go);padding:0.1rem;\">&#8595;</div>"
        "<div style=\"background:var(--dk);border-radius:6px;padding:0.8rem 1rem;border-left:3px solid var(--go);\">"
        "<div style=\"font-size:0.55rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.3rem;\">After</div>"
        "<p style=\"font-size:0.72rem;\">One session. Five steps. A deploy-ready prompt you own and use on any platform.</p></div>"
        "<div style=\"background:rgba(224,184,72,0.06);border-radius:6px;padding:0.6rem 1rem;border:1px solid rgba(224,184,72,0.2);\">"
        "<p style=\"font-size:0.67rem;color:var(--go);font-weight:600;text-align:center;\">Works in n8n &middot; Claude &middot; Make &middot; Zapier &middot; Any model</p>"
        "</div></div>"
    )
    h = h[:start] + new4 + h[end:]
    print("S4 OK")
else:
    print("S4 SKIP")

open(f, "w", encoding="utf-8").write(h)
print("Saved", len(h))
