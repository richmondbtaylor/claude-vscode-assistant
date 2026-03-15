html = (
'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
'<title>promptAnything.io - Keynote Pitch Deck</title>'
'<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700;800'
'&family=Montserrat:wght@400;500;600;700&family=Open+Sans:wght@300;400;600&display=swap" rel="stylesheet">'
'<style>'
'* { margin: 0; padding: 0; box-sizing: border-box; }'
':root { --dn: #000814; --dk: #1E2333; --ow: #E6E2DE; --wh: #FAFBFA; --go: #E0B848; --bl: #1894C9; }'
'html, body { background: var(--dn); color: var(--wh); font-family: \'Open Sans\', Georgia, serif; }'
'@page { size: A4 landscape; margin: 0; }'
'.slide { width: 297mm; height: 210mm; background: var(--dn); position: relative; overflow: hidden;'
'  page-break-after: always; break-after: page; display: flex; flex-direction: column;'
'  padding: 12mm 15mm 16mm; -webkit-print-color-adjust: exact; print-color-adjust: exact; }'
'.slide:last-child { page-break-after: avoid; break-after: avoid; }'
'h1 { font-family: \'Poppins\',Arial,sans-serif; font-weight: 800; font-size: 2.8rem; line-height: 1.15; color: var(--wh); }'
'h2 { font-family: \'Poppins\',Arial,sans-serif; font-weight: 700; font-size: 1.8rem; line-height: 1.2; color: var(--wh); }'
'p, li { font-family: \'Open Sans\',Georgia,serif; font-size: 0.86rem; line-height: 1.6; color: var(--ow); }'
'.sn { position: absolute; bottom: 5mm; left: 15mm; font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.57rem; color: var(--ow); opacity: 0.28; }'
'.bm { position: absolute; bottom: 5mm; right: 15mm; font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.57rem; color: var(--ow); opacity: 0.28; text-transform: uppercase; }'
'.sl { font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.6rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.18em; color: var(--bl); margin-bottom: 0.4rem; }'
'.gr { width: 38px; height: 3px; background: var(--go); margin-bottom: 0.9rem; }'
'.br { width: 38px; height: 3px; background: var(--bl); margin-bottom: 0.9rem; }'
'.bul { list-style: none; margin-top: 0.85rem; }'
'.bul li { display: flex; align-items: flex-start; margin-bottom: 0.55rem; font-size: 0.85rem; color: var(--ow); }'
'.bul li::before { content: ""; display: inline-block; width: 5px; height: 5px; min-width: 5px; background: var(--go); margin-top: 0.48rem; margin-right: 0.7rem; }'
'.tc { display: flex; flex: 1; gap: 1.8rem; align-items: center; }'
'.cl { flex: 6; } .cr { flex: 4; display: flex; align-items: center; justify-content: center; }'
'.bdg { width: 105px; height: 105px; border-radius: 50%; border: 3px solid var(--go); display: flex; flex-direction: column; align-items: center; justify-content: center; background: rgba(224,184,72,0.07); }'
'.bdg .bn { font-family: \'Poppins\',Arial,sans-serif; font-size: 2.6rem; font-weight: 800; color: var(--go); line-height: 1; }'
'.bdg .bs { font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.53rem; font-weight: 600; text-transform: uppercase; color: var(--ow); margin-top: 2px; }'
'.crd { background: var(--dk); border-radius: 7px; padding: 1rem 1.2rem; border-left: 3px solid var(--go); }'
'.threec { display: flex; gap: 1rem; flex: 1; margin-top: 0.65rem; }'
'.th { flex: 1; background: var(--dk); border-radius: 6px; padding: 0.95rem; }'
'.ch { font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.6rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.6rem; padding-bottom: 0.38rem; border-bottom: 2px solid; }'
'.ch.p { color: #E05252; border-color: #E05252; } .ch.s { color: var(--go); border-color: var(--go); } .ch.r { color: var(--bl); border-color: var(--bl); }'
'.uc { background: var(--dk); border-radius: 8px; padding: 1.6rem; border-top: 3px solid var(--go); flex: 1; margin-top: 0.65rem; }'
'.uct { font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.56rem; font-weight: 700; text-transform: uppercase; color: var(--bl); margin-bottom: 0.32rem; }'
'.tag { background: var(--dk); border-radius: 16px; padding: 0.28rem 0.75rem; font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.6rem; font-weight: 600; display: inline-block; }'
'.tg { color: var(--go); border: 1px solid rgba(224,184,72,0.3); } .tb { color: var(--bl); border: 1px solid rgba(24,148,201,0.3); } .tm { color: var(--ow); border: 1px solid rgba(230,226,222,0.2); }'
'.bg1 { position: absolute; right: -45px; top: -45px; width: 200px; height: 200px; border-radius: 50%; background: rgba(224,184,72,0.033); pointer-events: none; }'
'.bg2 { position: absolute; right: 65px; bottom: 22px; width: 118px; height: 118px; border-radius: 50%; background: rgba(24,148,201,0.033); pointer-events: none; }'
'.ctb { background: rgba(224,184,72,0.07); border: 1px solid var(--go); border-radius: 7px; padding: 1.1rem 1.6rem; margin-top: 1rem; }'
'.ctl { font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.88rem; font-weight: 600; color: var(--go); margin-bottom: 0.28rem; }'
'.cts { font-family: \'Open Sans\',Georgia,serif; font-size: 0.75rem; color: var(--ow); }'
'.qr { width: 65px; height: 65px; border: 2px solid var(--go); border-radius: 4px; display: flex; align-items: center; justify-content: center; font-family: \'Montserrat\',Helvetica,sans-serif; font-size: 0.4rem; color: var(--go); text-align: center; line-height: 1.3; }'
'.ws { font-size: 0.46rem; font-family: \'Montserrat\',Helvetica,sans-serif; font-weight: 700; text-transform: uppercase; flex: 1; text-align: center; }'
'.ar { font-size: 0.95rem; color: var(--go); display: flex; align-items: center; }'
'</style></head><body>'
)

slides = []

# S1 Title
slides.append(
'<section class="slide">'
'<div class="bg1"></div><div class="bg2"></div>'
'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;max-width:64%;">'
'<div class="sl">Pitch Deck &middot; 2026</div>'
'<div class="gr"></div>'
'<h1 style="font-size:2.85rem;margin-bottom:0.95rem;">The AI idea was<br>never the problem.</h1>'
'<p style="font-size:1rem;color:var(--ow);max-width:440px;margin-bottom:1.6rem;">The prompt always was. Five steps. Any idea. Any platform.</p>'
'<div style="display:flex;align-items:center;gap:0.85rem;">'
'<span style="font-family:\'Poppins\',Arial,sans-serif;font-weight:800;font-size:1.3rem;color:var(--go);">promptAnything.io</span>'
'<span style="width:1px;height:19px;background:var(--ow);opacity:0.2;"></span>'
'<span style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.6rem;color:var(--ow);opacity:0.48;letter-spacing:0.1em;text-transform:uppercase;">Prompt Engineering &middot; Simplified</span>'
'</div></div>'
'<div class="sn">01</div><div class="bm">promptAnything.io</div>'
'</section>'
)

# S2 Exec Summary
slides.append(
'<section class="slide"><div class="bg1"></div>'
'<div class="sl">At a Glance</div>'
'<h2 style="font-size:1.5rem;margin-bottom:0.32rem;">Everyone has an AI idea. Most never ship. Here&rsquo;s why &mdash; and the fix.</h2>'
'<div style="display:flex;align-items:center;gap:0.7rem;margin:0.55rem 0 0.75rem;">'
'<div style="width:30px;height:2px;background:var(--go);"></div>'
'<span style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.64rem;color:var(--go);font-weight:700;">11 REWRITES.</span>'
'<span style="font-size:0.7rem;color:var(--ow);">The average person rewrites the same prompt 11 times before giving up. promptAnything.io eliminates every one of them.</span>'
'</div>'
'<div class="threec">'
'<div class="th"><div class="ch p">The Problem</div><ul class="bul" style="margin-top:0;"><li>Prompt engineering is a hidden skill barrier</li><li>Ideas die in endless iteration</li></ul></div>'
'<div class="th"><div class="ch s">The Solution</div><ul class="bul" style="margin-top:0;"><li>5-step guided prompt builder</li><li>Platform asks the questions you don&rsquo;t know to ask</li></ul></div>'
'<div class="th"><div class="ch r">The Result</div><ul class="bul" style="margin-top:0;"><li>Deploy-ready prompts in one session</li><li>Works in n8n, Make, Claude, and more</li></ul></div>'
'</div>'
'<div class="sn">02</div><div class="bm">promptAnything.io</div></section>'
)

# S3 Problem
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">The Problem</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>Most AI ideas die before they&rsquo;re built.</h2>'
'<ul class="bul"><li>The idea is clear. The prompt is not.</li><li>Iteration without structure wastes hours</li><li>The gap between idea and output is the prompt</li></ul>'
'<p style="margin-top:1rem;font-size:0.8rem;max-width:370px;">The models are extraordinary. GPT-4, Claude, Gemini &mdash; they can do almost anything you ask. The problem is the ask. Nobody taught you prompt engineering. The gap between your idea and a working AI product is filled with guesswork.</p>'
'</div><div class="cr"><div style="text-align:center;">'
'<div style="font-family:\'Poppins\',Arial,sans-serif;font-size:4.4rem;font-weight:800;color:var(--go);line-height:1;">11&times;</div>'
'<div style="font-size:0.75rem;color:var(--ow);margin-top:0.42rem;max-width:158px;text-align:center;line-height:1.4;">Average rewrites before a user abandons their AI idea</div>'
'</div></div></div>'
'<div class="sn">03</div><div class="bm">promptAnything.io</div></section>'
)

# S4 Solution
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">The Solution</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>promptAnything.io builds your prompt for you.</h2>'
'<ul class="bul"><li>Start with a simple idea</li><li>The platform asks the right questions</li><li>One click generates a deployment-ready prompt</li></ul>'
'<p style="margin-top:1rem;font-size:0.8rem;max-width:370px;">Not a prompt library. Not a template engine. An interactive prompt architect &mdash; walks you through a structured conversation, then delivers a finished prompt you can take anywhere.</p>'
'</div><div class="cr"><div style="display:flex;flex-direction:column;gap:0.55rem;width:100%;">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--ow);opacity:0.45;margin-bottom:0.1rem;">Before vs. After</div>'
'<div style="background:rgba(224,80,80,0.08);border-radius:6px;padding:0.75rem 0.9rem;border-left:3px solid #E05252;">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:#E05252;margin-bottom:0.28rem;">Without promptAnything</div>'
'<p style="font-size:0.71rem;line-height:1.5;">Blank page. 11 rewrites. Hours spent guessing at structure. Most ideas stall here.</p>'
'</div>'
'<div style="background:rgba(224,184,72,0.07);border-radius:6px;padding:0.75rem 0.9rem;border-left:3px solid var(--go);">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.28rem;">With promptAnything</div>'
'<p style="font-size:0.71rem;line-height:1.5;">5 guided steps. One session. A structured, deploy-ready prompt with no guesswork.</p>'
'</div>'
'</div></div></div>'
'<div class="sn">04</div><div class="bm">promptAnything.io</div></section>'
)

# S5 Workflow
step_cards = ""
steps = [("01","IDEA","Start with a simple idea &mdash; one sentence is enough","go"),
         ("02","PATH","Choose agent workflow or Claude skill","go"),
         ("03","REFINE","Platform asks and answers the right questions","go"),
         ("04","GENERATE","One click builds the full structured framework","go"),
         ("05","DEPLOY","Paste into any tool. Fully portable output.","bl")]
for i,(num,name,desc,col) in enumerate(steps):
    step_cards += (
        f'<div style="flex:1;background:var(--dk);border-radius:7px;padding:0.95rem;border-top:3px solid var(--{col});">'
        f'<div style="font-family:\'Poppins\',Arial,sans-serif;font-size:1.75rem;font-weight:800;color:var(--{col});line-height:1;">{num}</div>'
        f'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.62rem;font-weight:700;text-transform:uppercase;color:var(--wh);margin:0.38rem 0 0.28rem;">{name}</div>'
        f'<p style="font-size:0.74rem;">{desc}</p></div>'
    )
    if i < 4:
        step_cards += '<div class="ar">&#8594;</div>'
slides.append(
'<section class="slide"><div class="sl">The promptAnything Workflow</div>'
'<h2 style="margin-bottom:0.32rem;">Five steps. Every idea. Every platform.</h2>'
'<div style="width:32px;height:2px;background:var(--go);margin-bottom:1rem;"></div>'
f'<div style="display:flex;align-items:stretch;gap:0.5rem;flex:1;">{step_cards}</div>'
'<div class="sn">05</div><div class="bm">promptAnything.io</div></section>'
)

# S6 Step 1
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Step 01 of 05</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>You already have everything step one needs.</h2>'
'<ul class="bul"><li>One sentence minimum</li><li>No technical framing required</li><li>Any domain: business, content, automation</li></ul>'
'<div class="crd" style="margin-top:1.2rem;">'
'<p style="font-size:0.81rem;font-style:italic;">&ldquo;I want an AI that screens my inbound leads before I get on a call with them.&rdquo;</p>'
'<p style="font-size:0.68rem;color:var(--go);margin-top:0.38rem;font-family:\'Montserrat\',Helvetica,sans-serif;font-weight:600;">That&rsquo;s all step one needs.</p>'
'</div></div>'
'<div class="cr"><div class="bdg"><span class="bn">01</span><span class="bs">IDEA</span></div></div></div>'
'<div class="sn">06</div><div class="bm">promptAnything.io</div></section>'
)

# S7 Step 2
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Step 02 of 05</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>Two paths. One decision. No wrong answer.</h2>'
'<ul class="bul"><li>Agent workflow automation: multi-step, tool-connected</li><li>Claude skill: single-purpose, conversation-embedded</li><li>The choice shapes the entire prompt structure</li></ul>'
'<p style="margin-top:0.95rem;font-size:0.8rem;">Most people never think about this distinction before writing. That single decision changes everything about the prompt that gets built.</p>'
'</div><div class="cr"><div style="display:flex;flex-direction:column;gap:0.65rem;width:100%;">'
'<div style="background:var(--dk);border-radius:6px;padding:0.9rem;border-left:3px solid var(--go);">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.6rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.28rem;">Agent Workflow</div>'
'<p style="font-size:0.7rem;margin-bottom:0.3rem;">n8n &middot; Make &middot; Zapier &middot; Custom agents</p>'
'<p style="font-size:0.67rem;color:var(--ow);opacity:0.72;">Best when: you need multi-step automation, tool connections, or scheduled triggers. The prompt controls the agent logic end-to-end.</p>'
'</div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.9rem;border-left:3px solid var(--bl);">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.6rem;font-weight:700;text-transform:uppercase;color:var(--bl);margin-bottom:0.28rem;">Claude Skill</div>'
'<p style="font-size:0.7rem;margin-bottom:0.3rem;">Repeatable &middot; Conversation-embedded &middot; Single-purpose</p>'
'<p style="font-size:0.67rem;color:var(--ow);opacity:0.72;">Best when: you want consistent, reusable behavior in Claude conversations. The prompt defines the skill trigger and output format.</p>'
'</div>'
'</div></div></div>'
'<div class="sn">07</div><div class="bm">promptAnything.io</div></section>'
)

# S8 Step 3
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Step 03 of 05</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>The platform asks what you forgot to think about.</h2>'
'<ul class="bul"><li>Relevant questions auto-generated to your idea</li><li>Fills in context, constraints, and logic gaps</li><li>No prompt engineering knowledge required</li></ul>'
'<p style="margin-top:0.95rem;font-size:0.8rem;">It doesn&rsquo;t just ask &mdash; it answers alongside you. Compressed into a guided conversation anyone can complete.</p>'
'</div><div class="cr"><div style="display:flex;flex-direction:column;gap:0.48rem;width:100%;">'
'<div style="background:var(--dk);border-radius:5px;padding:0.58rem 0.82rem;font-size:0.69rem;color:var(--ow);border-left:2px solid var(--go);">Who is the audience for this output?</div>'
'<div style="background:var(--dk);border-radius:5px;padding:0.58rem 0.82rem;font-size:0.69rem;color:var(--ow);border-left:2px solid var(--go);">What format should the AI use?</div>'
'<div style="background:var(--dk);border-radius:5px;padding:0.58rem 0.82rem;font-size:0.69rem;color:var(--ow);border-left:2px solid var(--go);">What should it never do?</div>'
'<div style="background:var(--dk);border-radius:5px;padding:0.58rem 0.82rem;font-size:0.69rem;color:var(--ow);border-left:2px solid var(--go);">What&rsquo;s the success condition?</div>'
'</div></div></div>'
'<div class="sn">08</div><div class="bm">promptAnything.io</div></section>'
)

# S9 Step 4
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Step 04 of 05</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>One click builds the full structured framework.</h2>'
'<ul class="bul"><li>Complete prompt generated from your refined idea</li><li>Structured format &mdash; not freeform text</li><li>No editing required &mdash; deploy-ready on output</li></ul>'
'<p style="margin-top:0.95rem;font-size:0.8rem;">A framework with context blocks, instruction sets, constraints, and output format specs. Everything a prompt needs to work consistently.</p>'
'</div><div class="cr"><div style="text-align:center;display:flex;flex-direction:column;align-items:center;gap:0.65rem;">'
'<div style="width:100px;height:40px;background:var(--go);border-radius:5px;display:flex;align-items:center;justify-content:center;"><span style="font-family:\'Poppins\',Arial,sans-serif;font-weight:700;font-size:0.75rem;color:var(--dn);">Generate Prompt</span></div>'
'<div style="font-size:1.15rem;color:var(--go);">&#8595;</div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.65rem 0.85rem;font-size:0.64rem;color:var(--ow);text-align:left;width:100%;line-height:1.65;">'
'<span style="color:var(--go);">[CONTEXT]</span> You are a...<br>'
'<span style="color:var(--bl);">[INSTRUCTION]</span> When given...<br>'
'<span style="color:var(--go);">[CONSTRAINTS]</span> Never...<br>'
'<span style="color:var(--bl);">[OUTPUT FORMAT]</span> Return as...'
'</div></div></div></div>'
'<div class="sn">09</div><div class="bm">promptAnything.io</div></section>'
)

# S10 Step 5
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Step 05 of 05</div>'
'<div class="tc"><div class="cl"><div class="br"></div>'
'<h2>The prompt works in any tool you already use.</h2>'
'<ul class="bul"><li>Drop into n8n, Make, Zapier, or any agent</li><li>Use in Claude skills, web apps, custom workflows</li><li>One prompt. Total portability.</li></ul>'
'<p style="margin-top:0.95rem;font-size:0.8rem;">You&rsquo;re not locked into our platform. You&rsquo;re building assets you own. Every new platform becomes another deployment target.</p>'
'</div><div class="cr"><div style="display:grid;grid-template-columns:1fr 1fr;gap:0.45rem;width:100%;">'
'<div style="background:var(--dk);border-radius:6px;padding:0.62rem 0.75rem;border-top:2px solid var(--go);">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.18rem;">n8n</div>'
'<p style="font-size:0.65rem;opacity:0.75;">Paste prompt into AI node &rarr; done</p></div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.62rem 0.75rem;border-top:2px solid var(--go);">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.18rem;">Make</div>'
'<p style="font-size:0.65rem;opacity:0.75;">Drop into scenario module</p></div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.62rem 0.75rem;border-top:2px solid var(--bl);">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--bl);margin-bottom:0.18rem;">Claude Skills</div>'
'<p style="font-size:0.65rem;opacity:0.75;">Load as a reusable conversation skill</p></div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.62rem 0.75rem;border-top:2px solid var(--bl);">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--bl);margin-bottom:0.18rem;">Any Model</div>'
'<p style="font-size:0.65rem;opacity:0.75;">ChatGPT, Gemini, custom API</p></div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.62rem 0.75rem;border-top:2px solid rgba(230,226,222,0.3);grid-column:span 2;">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--ow);margin-bottom:0.18rem;">Web Apps &middot; API Pipelines &middot; Zapier &middot; Custom Agents</div>'
'<p style="font-size:0.65rem;opacity:0.75;">Your prompt is a portable asset. One session, infinite deployment targets.</p></div>'
'</div></div></div>'
'<div class="sn">10</div><div class="bm">promptAnything.io</div></section>'
)

# S11 Who
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Who It&rsquo;s For</div>'
'<h2 style="margin-bottom:0.32rem;">Built for builders who are not yet technical.</h2>'
'<div style="width:32px;height:2px;background:var(--go);margin-bottom:0.85rem;"></div>'
'<div style="display:flex;gap:1rem;flex:1;margin-top:0;">'
'<div class="th" style="border-top:3px solid var(--go);"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.6rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.42rem;">Founders</div><p style="font-size:0.76rem;">AI is on the roadmap. Building it keeps hitting a wall at the prompt layer. promptAnything.io removes that wall.</p></div>'
'<div class="th" style="border-top:3px solid var(--go);"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.6rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.42rem;">Operators</div><p style="font-size:0.76rem;">Five automation ideas, three months of Zapier experience. Knows the tools but not how to structure a prompt that controls the output.</p></div>'
'<div class="th" style="border-top:3px solid var(--go);"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.6rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.42rem;">Agencies</div><p style="font-size:0.76rem;">Delivering AI solutions to clients. Cannot spend eight hours per project on prompts through trial and error.</p></div>'
'</div>'
'<div class="sn">11</div><div class="bm">promptAnything.io</div></section>'
)

# S12 Market
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Market Opportunity</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>Prompt engineering is the new interface layer.</h2>'
'<ul class="bul"><li>Billions in AI spend failing at the prompt layer</li><li>Non-technical builders are the fastest-growing AI user segment</li><li>Platform-agnostic tools compound across every AI deployment</li></ul>'
'<p style="margin-top:0.95rem;font-size:0.8rem;">The model can do anything &mdash; the prompt is the constraint. Every new platform is a new deployment target. The market grows as AI grows.</p>'
'</div><div class="cr"><div style="display:flex;flex-direction:column;gap:0.5rem;width:100%;">'
'<div style="background:var(--dk);border-radius:7px;padding:0.75rem 0.9rem;border-left:3px solid var(--go);display:flex;align-items:center;gap:0.9rem;">'
'<div style="font-family:\'Poppins\',Arial,sans-serif;font-size:1.85rem;font-weight:800;color:var(--go);line-height:1;min-width:60px;">73M+</div>'
'<div><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--go);">Non-technical builders</div><p style="font-size:0.67rem;margin-top:0.1rem;">actively using automation tools today &mdash; all hitting the prompt wall</p></div>'
'</div>'
'<div style="background:var(--dk);border-radius:7px;padding:0.75rem 0.9rem;border-left:3px solid var(--go);display:flex;align-items:center;gap:0.9rem;">'
'<div style="font-family:\'Poppins\',Arial,sans-serif;font-size:1.85rem;font-weight:800;color:var(--go);line-height:1;min-width:60px;">$390B</div>'
'<div><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--go);">AI tooling market by 2028</div><p style="font-size:0.67rem;margin-top:0.1rem;">Prompt infrastructure is the fastest-growing layer</p></div>'
'</div>'
'<div style="background:var(--dk);border-radius:7px;padding:0.75rem 0.9rem;border-left:3px solid var(--bl);display:flex;align-items:center;gap:0.9rem;">'
'<div style="font-family:\'Poppins\',Arial,sans-serif;font-size:1.85rem;font-weight:800;color:var(--bl);line-height:1;min-width:60px;">11&times;</div>'
'<div><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--bl);">Avg. rewrites before abandonment</div><p style="font-size:0.67rem;margin-top:0.1rem;">Every one of them is a conversion we capture</p></div>'
'</div>'
'</div></div></div>'
'<div class="sn">12</div><div class="bm">promptAnything.io</div></section>'
)

# S13 Why Now
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Why Now</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>Non-technical builders are running out of excuses not to build.</h2>'
'<ul class="bul"><li>Models are capable. Prompts are the last barrier.</li><li>Workflow tools democratized automation &mdash; this democratizes prompts</li><li>The window for platform-agnostic tooling is open</li></ul>'
'</div><div class="cr"><div style="display:flex;flex-direction:column;gap:0.6rem;width:100%;">'
'<div style="background:var(--dk);border-radius:6px;padding:0.7rem 0.9rem;display:flex;gap:0.65rem;"><span style="color:var(--go);font-weight:700;font-family:\'Poppins\',Arial,sans-serif;min-width:15px;">1</span><p style="font-size:0.72rem;">Models got good enough. The capability ceiling is gone for most use cases.</p></div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.7rem 0.9rem;display:flex;gap:0.65rem;"><span style="color:var(--go);font-weight:700;font-family:\'Poppins\',Arial,sans-serif;min-width:15px;">2</span><p style="font-size:0.72rem;">Workflow platforms matured. Millions of non-technical builders already use automation tools.</p></div>'
'<div style="background:var(--dk);border-radius:6px;padding:0.7rem 0.9rem;display:flex;gap:0.65rem;border-left:2px solid var(--go);"><span style="color:var(--go);font-weight:700;font-family:\'Poppins\',Arial,sans-serif;min-width:15px;">3</span><p style="font-size:0.72rem;color:var(--go);font-weight:600;font-family:\'Montserrat\',Helvetica,sans-serif;">Nobody solved the prompt layer for those people &mdash; until now.</p></div>'
'</div></div></div>'
'<div class="sn">13</div><div class="bm">promptAnything.io</div></section>'
)

# S14 Use Case 1
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Use Case &middot; Agent Workflow Automation</div>'
'<div class="uc" style="border-top-color:var(--go);">'
'<div class="uct">Agent Workflow Automation</div>'
'<h2 style="margin-bottom:0.8rem;font-size:1.6rem;">From idea to deployed lead qualifier in one session.</h2>'
'<div style="display:flex;gap:1.1rem;margin-top:0.3rem;">'
'<div style="flex:1;"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.56rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.38rem;">The Idea</div><p style="font-size:0.76rem;font-style:italic;">&ldquo;Screen my inbound leads before I get on a call with them.&rdquo;</p></div>'
'<div style="width:1px;background:rgba(255,255,255,0.07);"></div>'
'<div style="flex:1;"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.56rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.38rem;">The Result</div><ul class="bul" style="margin-top:0;"><li>Deployed in n8n same day</li><li>Connected to intake form + CRM</li><li>Zero iterations after generate</li></ul></div>'
'<div style="width:1px;background:rgba(255,255,255,0.07);"></div>'
'<div style="flex:1;text-align:center;"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.56rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.38rem;">Time to Deploy</div><div style="font-family:\'Poppins\',Arial,sans-serif;font-size:2.2rem;font-weight:800;color:var(--go);line-height:1;">15<span style="font-size:0.88rem;color:var(--ow);font-weight:400;"> min</span></div><p style="font-size:0.68rem;margin-top:0.25rem;">idea to running workflow</p></div>'
'</div></div>'
'<div class="sn">14</div><div class="bm">promptAnything.io</div></section>'
)

# S15 Use Case 2
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">Use Case &middot; Claude Skill</div>'
'<div class="uc" style="border-top-color:var(--bl);">'
'<div class="uct" style="color:var(--bl);">Claude Skill</div>'
'<h2 style="margin-bottom:0.8rem;font-size:1.6rem;">A client-facing content skill built in one afternoon.</h2>'
'<div style="display:flex;gap:1.1rem;margin-top:0.3rem;">'
'<div style="flex:1;"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.56rem;font-weight:700;text-transform:uppercase;color:var(--bl);margin-bottom:0.38rem;">The Idea</div><p style="font-size:0.76rem;font-style:italic;">&ldquo;Turn any meeting transcript into a follow-up email in my client&rsquo;s brand voice.&rdquo;</p></div>'
'<div style="width:1px;background:rgba(255,255,255,0.07);"></div>'
'<div style="flex:1;"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.56rem;font-weight:700;text-transform:uppercase;color:var(--bl);margin-bottom:0.38rem;">The Result</div><ul class="bul" style="margin-top:0;"><li>Loaded into Claude skill system</li><li>Consistent tone every invocation</li><li>Client-ready output, no editing</li></ul></div>'
'<div style="width:1px;background:rgba(255,255,255,0.07);"></div>'
'<div style="flex:1;text-align:center;"><div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.56rem;font-weight:700;text-transform:uppercase;color:var(--bl);margin-bottom:0.38rem;">Time to Deploy</div><div style="font-family:\'Poppins\',Arial,sans-serif;font-size:2.2rem;font-weight:800;color:var(--bl);line-height:1;">15<span style="font-size:0.88rem;color:var(--ow);font-weight:400;"> min</span></div><p style="font-size:0.68rem;margin-top:0.25rem;">idea to repeatable skill</p></div>'
'</div></div>'
'<div class="sn">15</div><div class="bm">promptAnything.io</div></section>'
)

# S16 CTA Setup
steps_list = ""
for n, label, col in [("1","Idea","go"),("2","Path","go"),("3","Refine","go"),("4","Generate","go"),("5","Deploy","bl")]:
    txt_col = "var(--go)" if col == "go" else "var(--wh)"
    label_style = f'font-size:0.76rem;color:{"var(--go);font-weight:600;font-family:\'Montserrat\',Helvetica,sans-serif;" if n=="5" else "var(--ow);"}'
    steps_list += (
        f'<div style="display:flex;align-items:center;gap:0.48rem;padding:0.32rem 0;">'
        f'<span style="width:19px;height:19px;background:var(--{col});border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:\'Poppins\',Arial,sans-serif;font-size:0.56rem;font-weight:700;color:{txt_col};min-width:19px;">{n}</span>'
        f'<span style="{label_style}">{label}</span></div>'
    )
slides.append(
'<section class="slide"><div class="bg1"></div><div class="sl">The Ask</div>'
'<div class="tc"><div class="cl"><div class="gr"></div>'
'<h2>You already have the idea. You know where the gap is.</h2>'
'<ul class="bul"><li>The prompt is the only thing between you and shipping</li><li>You now have a five-step system to close that gap</li><li>One session. One prompt. Everything changes.</li></ul>'
'<p style="margin-top:0.95rem;font-size:0.8rem;">The one AI idea you&rsquo;ve been sitting on &mdash; half-built in your head for weeks &mdash; is one session away from being real.</p>'
f'</div><div class="cr"><div style="display:flex;flex-direction:column;gap:0.55rem;width:100%;">'
'<div style="background:rgba(224,184,72,0.07);border:1px solid rgba(224,184,72,0.3);border-radius:7px;padding:0.85rem 1rem;">'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.52rem;font-weight:700;text-transform:uppercase;color:var(--go);margin-bottom:0.45rem;">What you walk away with</div>'
'<ul class="bul" style="margin-top:0;">'
'<li style="font-size:0.72rem;">A structured, deploy-ready prompt</li>'
'<li style="font-size:0.72rem;">Zero iterations required after generate</li>'
'<li style="font-size:0.72rem;">Works in any tool you already use</li>'
'<li style="font-size:0.72rem;">Repeatable &mdash; run again on any new idea</li>'
'</ul>'
'</div>'
'<div style="background:var(--dk);border-radius:7px;padding:0.75rem 1rem;text-align:center;">'
'<div style="font-family:\'Poppins\',Arial,sans-serif;font-size:0.8rem;font-weight:700;color:var(--wh);margin-bottom:0.2rem;">No account needed to start.</div>'
'<div style="font-family:\'Montserrat\',Helvetica,sans-serif;font-size:0.62rem;color:var(--go);font-weight:600;">promptAnything.io &rarr; open &rarr; build</div>'
'</div>'
'</div></div></div>'
'<div class="sn">16</div><div class="bm">promptAnything.io</div></section>'
)

# S17 Closing
arrow_bar = ""
wf_labels = [("IDEA","go"),("PATH","go"),("REFINE","go"),("GENERATE","go"),("DEPLOY","bl")]
for i,(lbl,col) in enumerate(wf_labels):
    arrow_bar += f'<div class="ws" style="color:var(--{col});">{lbl}</div>'
    if i < 4:
        arrow_bar += f'<div style="height:1px;flex:2;background:var(--go);position:relative;"><div style="position:absolute;right:-4px;top:-4px;width:0;height:0;border-left:6px solid var(--go);border-top:4px solid transparent;border-bottom:4px solid transparent;"></div></div>'
slides.append(
'<section class="slide" style="justify-content:center;align-items:center;">'
'<div class="bg1"></div><div class="bg2"></div>'
'<div style="text-align:center;max-width:475px;margin:0 auto;">'
'<div class="sl" style="text-align:center;">Start Today</div>'
'<h1 style="font-size:2.4rem;margin-bottom:0.82rem;">Try the workflow on your idea today.</h1>'
'<div style="width:38px;height:2px;background:var(--go);margin:0 auto 1.1rem;"></div>'
'<div class="ctb" style="max-width:350px;margin:0 auto 1.1rem;">'
'<div class="ctl">1. Go to promptAnything.io</div>'
'<div class="cts">Choose your path. Run the workflow.</div>'
'<div class="ctl" style="margin-top:0.38rem;">2. Walk out with a deployment-ready prompt.</div>'
'<div class="cts">One session. No guesswork. No iterations.</div>'
'</div>'
'<div style="display:flex;align-items:center;justify-content:center;gap:1.1rem;">'
'<span style="font-family:\'Poppins\',Arial,sans-serif;font-weight:800;font-size:1.15rem;color:var(--go);">promptAnything.io</span>'
'<div class="qr">QR<br>CODE</div>'
'</div></div>'
f'<div style="position:absolute;bottom:13mm;left:15mm;right:15mm;display:flex;align-items:center;">{arrow_bar}</div>'
'<div class="sn">17</div><div class="bm">promptAnything.io</div></section>'
)

full_html = html + "".join(slides) + "</body></html>"
out = "C:/Users/richm/.claude/2026-03-13 promptAnything.io - Keynote Pitch Deck.html"
with open(out, "w", encoding="utf-8") as f:
    f.write(full_html)
print(f"Written: {len(full_html)} chars to {out}")
