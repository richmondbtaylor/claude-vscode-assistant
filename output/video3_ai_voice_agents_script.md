# SCRIPTFORGE OUTPUT

## Topic Suitability Assessment

Strong dual-format fit. The voice agent vs. chatbot distinction, the live build walkthrough, and the pricing breakdown each produce self-contained Shorts. The long-form narrative builds logically from concept to build to monetization -- a complete journey for the viewer. Four Shorts identified.

---

```
=====================================================================
  AI VOICE AGENTS ARE HERE -- HOW TO BUILD ONE IN 30 MINUTES
  YouTube Chapter Markers
=====================================================================

00:00 - Your Competitors Are Already Using AI Voice Agents
01:48 - Voice Agents vs. Chatbots: Why It Matters
04:15 - The Live Build: Setting Up Your First Voice Agent
09:30 - Connecting to CRM & Calendar for Real Bookings
13:45 - Handling Objections with Prompt Engineering
17:30 - Pricing This as a Service: What to Charge Clients
21:00 - The Bigger Picture: Where Voice AI Goes Next
22:30 - Full Walkthrough + Templates


-- INTRO ---------------------------------------------------------------

00:00.000 [CAMERA: Medium shot, Richmond at desk, direct to camera]
00:00.000 [TEXT ON-SCREEN: "Your competitors are answering calls with AI right now."]

RICHMOND: Your competitors are answering calls with AI right now. Not next year. Not "eventually." Right now. While you're sending callers to voicemail or paying someone $18 an hour to say "let me check on that and get back to you" -- businesses down the street have AI picking up on the first ring, booking appointments, and qualifying leads at 2 AM on a Sunday.

00:18.000 [CAMERA: Slight push-in, tighter framing]
00:18.000 [B-ROLL: 3s -- Phone ringing, unanswered, going to voicemail]

RICHMOND: And here's what nobody talks about -- this isn't some enterprise-only, six-figure deployment anymore. You can build a working AI voice agent in 30 minutes. Today. In this video. I'm going to show you exactly how, step by step.

00:32.000 [GRAPHIC: Animated agenda list fading in item by item:
  1. Voice Agent vs. Chatbot
  2. Live Build with Retell AI
  3. CRM + Calendar Integration
  4. Objection Handling via Prompt Engineering
  5. How to Price This as a Service]

RICHMOND: We're covering the full stack -- what a voice agent actually is, building one live, connecting it to real business tools, engineering it to handle pushback, and then how to sell this as a service to clients. Let's get into it.

00:48.000 [CAMERA: Cut to wide shot, brief pause]

[RICHMOND -> AI]

RICHMOND: Before we build, I want to ground this in reality. Give us the numbers.

00:52.000 [CAMERA: Screen recording-style frame with AI co-host avatar]

AI: Gartner projected in 2024 that conversational AI deployments in contact centers will reduce agent labor costs by $80 billion by 2026. McKinsey estimates AI can automate 60 to 70 percent of routine customer service interactions. The conversational AI market hit roughly $10 to $12 billion in 2023 and is growing at a 23 to 25 percent compound annual growth rate through 2030, according to Grand View Research. This is not a niche -- it is a category shift in how businesses handle inbound communication.

01:18.000 [TEXT ON-SCREEN: "$80B in labor cost reduction by 2026 -- Gartner"]
01:22.000 [TEXT ON-SCREEN: "60-70% of routine interactions automatable -- McKinsey"]

[AI -> RICHMOND]

01:28.000 [CAMERA: Back to Richmond, medium shot]

RICHMOND: So the market is real, the money is real, and the tools to build this are accessible right now. That is the window we're operating in. Let's start with the concept.


-- MAIN CONTENT --------------------------------------------------------

  [SECTION 1: Voice Agents vs. Chatbots -- Why It Matters]

01:48.000 [CHAPTER: Voice Agents vs. Chatbots: Why It Matters]
01:48.000 [CAMERA: Medium shot, Richmond gesturing]

RICHMOND: Most people hear "AI agent" and think chatbot. A little widget on a website that says "How can I help you?" and then fails the second you ask anything real. A voice agent is a fundamentally different thing.

02:02.000 [GRAPHIC: Split screen animation --
  LEFT: "Chatbot" with text bubble interface, typed responses, menu buttons
  RIGHT: "Voice Agent" with phone icon, sound waves, real-time conversation flow]

RICHMOND: A chatbot is text-based. It waits for input. It follows branching logic -- if they say X, respond with Y. A voice agent operates in real-time over a phone call. It listens, processes natural language, generates responses, and speaks them back -- all with sub-second latency. It handles interruptions. It adjusts tone. It sounds like a human receptionist.

02:28.000 [CAMERA: Close-up]

RICHMOND: The difference matters because of where your customers actually are. Most local businesses -- dentists, HVAC companies, med spas, law firms -- their leads come in by phone. Not chat. Phone.

02:42.000 [B-ROLL: 4s -- Small business phone ringing, someone picking up]

[RICHMOND -> AI]

02:46.000 [CAMERA: AI co-host frame]

AI: To be precise about the underlying architecture -- a modern AI voice agent combines three layers. First, automatic speech recognition, or ASR, converts the caller's voice to text in real time. Second, a large language model processes that text, determines intent, and generates a response. Third, text-to-speech, or TTS, converts that response back to natural-sounding audio. Platforms like Retell AI and Vapi orchestrate all three layers with end-to-end latency under 800 milliseconds. That is fast enough that the caller perceives a natural conversational rhythm, not a delay.

03:18.000 [GRAPHIC: Animated pipeline diagram:
  Caller Voice -> ASR -> LLM Processing -> TTS -> Agent Voice
  With "< 800ms" label spanning the full pipeline]

[AI -> RICHMOND]

03:28.000 [CAMERA: Back to Richmond]

RICHMOND: And that latency piece is everything. If the response takes two or three seconds, the caller knows it is AI and hangs up. Under a second? They just think they're talking to a really sharp receptionist. That is the bar, and the platforms we're using today clear it.

03:44.000 [TEXT ON-SCREEN: "< 800ms response = natural conversation"]

RICHMOND: Now -- the two platforms I want you to know about. Retell AI and Vapi. Both let you build production-grade voice agents. Retell leans more toward a visual builder -- great if you're not a developer. Vapi is more API-first, bring-your-own-model -- more flexibility if you want to pick your LLM. For today's build, I'm using Retell because it's the fastest path from zero to working agent.

04:10.000 [GRAPHIC: Side-by-side comparison card:
  Retell AI: Visual builder, turnkey, <800ms latency, ~$0.07-0.12/min
  Vapi: API-first, bring-your-own-model, flexible, ~$0.05/min + LLM costs]


  [SECTION 2: The Live Build -- Setting Up Your First Voice Agent]

04:15.000 [CHAPTER: The Live Build: Setting Up Your First Voice Agent]
04:15.000 [CAMERA: Screen recording with Richmond picture-in-picture, bottom right]
04:15.000 [TEXT ON-SCREEN: "LIVE BUILD: AI Receptionist for a Med Spa"]

RICHMOND: Alright, let's build. I'm going to create an AI receptionist for a fictional med spa called "Glow Aesthetic Studio." This is one of the highest-demand use cases -- local service business, appointment-based, phone-heavy.

04:30.000 [VISUAL: Retell AI dashboard, creating a new agent]

RICHMOND: Step one -- sign up at Retell AI. Free tier gives you enough minutes to test. Once you're in, hit "Create Agent."

04:40.000 [VISUAL: Agent creation screen, naming it "Glow Aesthetic Receptionist"]

RICHMOND: Name your agent. I'm calling this one "Glow Aesthetic Receptionist." Now here's where it gets good -- the system prompt. This is the brain of your agent. Everything it knows, how it behaves, what it can and cannot say -- it all lives here.

04:58.000 [CAMERA: Cut to close-up of Richmond, direct to camera]

RICHMOND: I'm going to give you the exact prompt structure I use for every voice agent I build. This is the template.

05:06.000 [GRAPHIC: Animated text block building line by line:

  IDENTITY:
  "You are the front desk receptionist at Glow Aesthetic Studio..."

  RULES:
  "Never discuss pricing over the phone -- always book a consultation..."
  "If asked about a service you don't recognize, say you'll have the team follow up..."

  KNOWLEDGE:
  "Services offered: Botox, fillers, chemical peels, laser treatments..."
  "Hours: Monday-Friday 9am-6pm, Saturday 10am-3pm..."

  GOAL:
  "Your primary objective is to book a consultation appointment..."]

05:06.000 [TEXT ON-SCREEN: "The 4-Block Prompt: Identity / Rules / Knowledge / Goal"]

RICHMOND: Four blocks. Identity -- who is this agent? Rules -- what can it say and what is off-limits? Knowledge -- the facts it needs to do its job. Goal -- the one action you want every call to drive toward. For a med spa, that goal is always "book the consultation."

05:32.000 [VISUAL: Pasting prompt into Retell AI agent builder]

RICHMOND: I paste this into the system prompt field. Now let's pick a voice.

05:40.000 [VISUAL: Retell AI voice selection interface, previewing different voices]

RICHMOND: Retell gives you a voice library. You want something warm, professional, matches the brand. For a med spa, I'm going with a female voice, mid-range tone, conversational. Listen to the difference between these two --

05:55.000 [VISUAL: Playing two voice samples side by side]
05:55.000 [TEXT ON-SCREEN: "Voice A: Corporate / Formal" vs. "Voice B: Warm / Conversational"]

RICHMOND: Voice B. Every time. Match the voice to the vibe of the business. A law firm gets a different voice than a med spa.

06:10.000 [VISUAL: Selecting the voice, moving to test call interface]

RICHMOND: Now we test. Retell lets you make a test call directly in the browser. Watch this.

06:18.000 [VISUAL: Live test call playing out -- Richmond speaks as the "caller," the AI responds in real time]

RICHMOND (as caller): "Hi, I was wondering if you guys do Botox? I've never had it done before."

06:22.000 [VISUAL: AI agent responding naturally, offering to book a consultation]

RICHMOND: Hear that? Sub-second response. Stayed on script. Didn't quote a price -- because we told it not to. And it drove straight to booking. That's six minutes of work and we already have a functioning receptionist.

06:40.000 [TEXT ON-SCREEN: "6 minutes to a working AI receptionist"]

[RICHMOND -> AI]

06:44.000 [CAMERA: AI co-host frame]

AI: One technical note worth highlighting -- Retell AI uses what they call "custom function calling." This means your agent can trigger external API calls mid-conversation. It is not just responding with text. It can actively check availability, create a booking, or pull up a customer record while the caller is still on the line. That is the bridge between a demo and a production deployment.

07:08.000 [GRAPHIC: Diagram showing: Caller speaks -> Agent processes -> Function call fires -> CRM/Calendar responds -> Agent confirms to caller]

[AI -> RICHMOND]

07:16.000 [CAMERA: Back to Richmond, screen recording]

RICHMOND: And that's exactly what we're going to do next -- connect this to real tools.


  [SECTION 3: Connecting to CRM & Calendar for Real Bookings]

09:30.000 [CHAPTER: Connecting to CRM & Calendar for Real Bookings]
09:30.000 [CAMERA: Screen recording with Richmond PIP]
09:30.000 [TEXT ON-SCREEN: "Making It Real: CRM + Calendar Integration"]

RICHMOND: A voice agent that talks well but can't book anything is a party trick. Let's make it real. I'm going to connect our agent to Cal.com for scheduling and GoHighLevel for the CRM. These are two of the most common tools in the agency space.

09:50.000 [VISUAL: Cal.com dashboard, showing API settings]

RICHMOND: In Cal.com, grab your API key. We need two things -- the ability to check available time slots and the ability to create a booking. Both are standard API endpoints.

10:08.000 [VISUAL: Retell AI custom function setup screen]

RICHMOND: Back in Retell, we set up custom functions. First function -- "check_availability." When the caller says "Do you have anything Thursday afternoon?" -- the agent fires this function, hits the Cal.com API, and gets back real open slots.

10:28.000 [GRAPHIC: Flow diagram:
  Caller: "Thursday afternoon?"
  -> Agent triggers check_availability()
  -> Cal.com API returns: [2:00 PM, 3:30 PM, 5:00 PM]
  -> Agent: "I have openings at 2, 3:30, and 5. Which works best?"]

RICHMOND: Second function -- "book_appointment." Once the caller picks a time, the agent collects their name, email, and phone number, then fires this function to create the booking in Cal.com. The caller gets a confirmation email. The business gets it on their calendar. Done.

10:55.000 [VISUAL: Retell AI function configuration with Cal.com webhook URL]

RICHMOND: Now for the CRM side. GoHighLevel -- or GHL as most agency owners know it -- has a direct integration path with Retell.

11:08.000 [VISUAL: GoHighLevel contact creation workflow]

RICHMOND: Every call creates or updates a contact in GHL. Name, phone, email, what they called about, whether they booked -- all of it flows in automatically. You can trigger follow-up sequences, tag the contact, assign them to a pipeline. The voice agent becomes the top of your sales funnel.

11:30.000 [TEXT ON-SCREEN: "Every call = CRM contact + calendar booking + follow-up trigger"]

[RICHMOND -> AI]

11:34.000 [CAMERA: AI co-host frame]

AI: For teams not using GoHighLevel, the same architecture works with any CRM that exposes an API. HubSpot, Salesforce, Zoho -- you route through Make.com or Zapier as middleware. Retell's custom function fires a webhook, Make catches it, and pushes the data to your CRM. The integration layer adds roughly 30 seconds of setup per connection and zero additional latency to the call itself.

11:58.000 [GRAPHIC: Architecture diagram:
  Retell Agent -> Webhook -> Make.com -> [HubSpot | Salesforce | Zoho]
  Retell Agent -> Direct API -> Cal.com / Calendly / GHL]

[AI -> RICHMOND]

12:08.000 [CAMERA: Back to Richmond]

RICHMOND: The point is -- this is not locked into one ecosystem. Whatever your client uses, you can wire it up. And that's a big part of why this is valuable as a service. You're not selling software. You're selling a complete system.

12:24.000 [VISUAL: Running another test call, this time showing the booking flow end-to-end]

RICHMOND: Let me run one more test call to show the full loop. I'll call in, ask about availability, pick a slot, and we'll watch the booking appear in Cal.com in real time.

12:36.000 [VISUAL: Test call plays out -- caller asks for Thursday, agent checks availability, offers slots, caller picks one, agent books it]

12:58.000 [VISUAL: Cal.com dashboard refreshes -- new appointment appears]

RICHMOND: There it is. Real booking. Real calendar entry. And the caller never knew they were talking to AI.

13:10.000 [TEXT ON-SCREEN: "Real booking. Real calendar. Zero human involvement."]

RICHMOND: Now -- the hard part. What happens when the caller pushes back?


  [SECTION 4: Handling Objections with Prompt Engineering]

13:45.000 [CHAPTER: Handling Objections with Prompt Engineering]
13:45.000 [CAMERA: Medium shot, Richmond at desk]

RICHMOND: Every caller who doesn't immediately say "yes, book me in" is going to have objections. "How much does it cost?" "I need to talk to my spouse." "Can I just get a callback?" If your voice agent fumbles these, you lose the lead. This is where prompt engineering separates a toy from a tool.

14:08.000 [TEXT ON-SCREEN: "Prompt Engineering = Objection Handling"]

RICHMOND: Let me show you the three most common objections and exactly how I engineer the prompt to handle each one.

14:16.000 [GRAPHIC: Objection #1 card fading in: "How much does it cost?"]

RICHMOND: Objection one -- pricing. For most service businesses, you do not want the AI quoting prices over the phone. The consultation is where the sale happens. So in the Rules block of our prompt, we write --

14:30.000 [VISUAL: Prompt text highlighted:
  "If the caller asks about pricing, acknowledge the question warmly, explain that pricing depends on their specific goals and skin type, and redirect to booking a free consultation where the specialist can give them an accurate quote."]

RICHMOND: The agent never stonewalls. It validates the question, gives a real reason why pricing needs to happen in person, and redirects. Watch --

14:48.000 [VISUAL: Test call clip -- caller asks "So how much is Botox?" -- agent responds naturally, redirects to consultation]

RICHMOND: Smooth. No awkward pause. No "I'm not able to help with that." Just a natural redirect.

15:00.000 [GRAPHIC: Objection #2 card: "I need to think about it / talk to my spouse"]

RICHMOND: Objection two -- the stall. "Let me think about it." Here's the prompt engineering --

15:08.000 [VISUAL: Prompt text highlighted:
  "If the caller hesitates or says they need time, acknowledge that this is a big decision. Offer to hold a tentative spot for them so they don't lose the time slot, and mention they can always reschedule. Reduce the commitment level."]

RICHMOND: You're not pressuring anyone. You're removing friction. "I can hold a tentative slot" is way easier to say yes to than "commit right now."

15:28.000 [GRAPHIC: Objection #3 card: "Can someone just call me back?"]

RICHMOND: Objection three -- the callback request. This one kills conversion if you let it. Every callback request is a lead that goes cold. Here's the prompt --

15:40.000 [VISUAL: Prompt text highlighted:
  "If the caller requests a callback, say: 'Absolutely, I can arrange that. While I have you, would you like me to pencil in a consultation time so you're guaranteed a spot? That way when we call back, we can confirm rather than start from scratch.'"]

RICHMOND: You honor the request, but you still drive toward the booking. The callback becomes a confirmation call, not a cold re-engagement.

15:58.000 [CAMERA: Close-up, direct to camera]

RICHMOND: This is the skill. Anyone can set up the tech. The people who win are the ones who think through every conversation path and engineer the prompt to handle it.

[RICHMOND -> AI]

16:08.000 [CAMERA: AI co-host frame]

AI: One framework worth adopting -- treat your prompt like a decision tree, but write it in natural language rather than rigid if-then logic. Large language models handle fuzzy intent matching far better than hardcoded branches. Instead of "if the caller says the word 'expensive,' respond with X," write "if the caller expresses concern about cost in any way." The LLM generalizes across phrasing. That is its core strength. Exploit it.

16:34.000 [TEXT ON-SCREEN: "Write rules as intent patterns, not keyword triggers"]

AI: Also -- test with adversarial calls. Have someone call your agent and deliberately try to break it. Ask off-topic questions. Interrupt mid-sentence. Give contradictory information. Every failure you find in testing is a conversion you save in production.

[AI -> RICHMOND]

16:52.000 [CAMERA: Back to Richmond]

RICHMOND: Hundred percent. I test every agent with at least 20 adversarial calls before it goes live. If it breaks, I fix the prompt. That testing phase is non-negotiable.

17:04.000 [TEXT ON-SCREEN: "20+ adversarial test calls before going live"]


  [SECTION 5: Pricing This as a Service -- What to Charge Clients]

17:30.000 [CHAPTER: Pricing This as a Service: What to Charge Clients]
17:30.000 [CAMERA: Medium shot, Richmond leaning forward]

RICHMOND: This is the part everyone asks about. You've built the agent. It works. Now what do you charge?

17:40.000 [TEXT ON-SCREEN: "The Business Model: AI Voice Agents as a Service"]

RICHMOND: I'm going to give you three pricing models that work right now in 2026. These are based on what I've seen agencies actually charge -- not theory.

17:52.000 [GRAPHIC: Pricing Model #1 card:
  "SETUP + MONTHLY RETAINER"
  Setup: $1,500 - $3,000
  Monthly: $500 - $1,000/mo
  Includes: Agent build, prompt engineering, integrations, ongoing optimization]

RICHMOND: Model one -- setup fee plus monthly retainer. You charge $1,500 to $3,000 to build the agent, connect the integrations, and do the prompt engineering. Then $500 to $1,000 per month for hosting, monitoring, and optimization. This is the bread and butter. Most agencies start here.

18:18.000 [GRAPHIC: Pricing Model #2 card:
  "PER-MINUTE USAGE"
  Rate: $0.50 - $1.00/min
  Your cost: ~$0.07-0.15/min
  Margin: 80-90%
  Best for: High-volume call centers]

RICHMOND: Model two -- per-minute pricing. You charge the client 50 cents to a dollar per minute of AI call time. Your actual cost on Retell or Vapi is 7 to 15 cents per minute. That's an 80 to 90 percent margin. This works best for clients with high call volume -- think property management companies, large dental practices, multi-location businesses.

18:46.000 [GRAPHIC: Pricing Model #3 card:
  "PER-BOOKING / PERFORMANCE"
  Rate: $15 - $50 per booked appointment
  Best for: Results-skeptical clients
  Risk: You eat the cost if the agent underperforms]

RICHMOND: Model three -- performance-based. You charge per booked appointment. $15 to $50 per booking, depending on the industry. This is a great door-opener for clients who are skeptical. You're saying "I only get paid when this works." The risk is on you, so your prompt engineering better be tight.

19:10.000 [CAMERA: Close-up]

RICHMOND: My recommendation? Start with model one. It's predictable, it's profitable, and it forces the client to commit. Once you have case studies, you can pitch model three to bigger clients as a land-and-expand strategy.

19:26.000 [TEXT ON-SCREEN: "Start with Setup + Retainer. Expand to Performance-Based."]

[RICHMOND -> AI]

19:30.000 [CAMERA: AI co-host frame]

AI: The unit economics are worth stating clearly. A human receptionist in the United States costs roughly $35,000 to $45,000 per year in salary alone -- before benefits, training, turnover costs, and the fact that they cannot answer calls at 2 AM. An AI voice agent operating 24/7 at moderate call volume costs the agency roughly $200 to $400 per month in platform fees. When you frame the value proposition to a client, you are not selling AI. You are selling a 24/7 employee that never calls in sick, at a fraction of the cost. That is the pitch.

20:02.000 [TEXT ON-SCREEN: "Human receptionist: ~$40K/yr | AI voice agent: ~$3-5K/yr"]
20:06.000 [GRAPHIC: Bar chart comparison -- Annual cost: Human vs. AI, with "24/7 coverage" label on the AI bar]

[AI -> RICHMOND]

20:14.000 [CAMERA: Back to Richmond]

RICHMOND: And that number sells itself. When you sit down with a business owner and show them that comparison, the conversation shifts from "should I do this?" to "how fast can you set it up?"

20:28.000 [CAMERA: Medium shot]

RICHMOND: One more thing on pricing -- always include a "prompt optimization" line item in your monthly retainer. Every month, you review call recordings, find where the agent struggled, and tighten the prompt. That ongoing optimization is what justifies the retainer and what keeps the client from trying to bring it in-house.

20:50.000 [TEXT ON-SCREEN: "Monthly prompt optimization = retainer justification"]


  [SECTION 6: The Bigger Picture]

21:00.000 [CHAPTER: The Bigger Picture: Where Voice AI Goes Next]
21:00.000 [CAMERA: Wide shot, Richmond standing]

RICHMOND: We built a voice agent in this video. But I want you to see the bigger picture. This is not a feature. This is an infrastructure shift. Every business that takes phone calls -- and that's most of them -- will have an AI handling at least the first touchpoint within the next 18 months. The early movers are building that right now.

21:22.000 [B-ROLL: 4s -- Montage of different business types: dental office, auto shop, real estate office, law firm]

RICHMOND: If you're an agency owner or a freelancer, this is one of the highest-leverage services you can offer in 2026. The build takes 30 minutes. The integrations take an afternoon. The value to the client is tens of thousands of dollars a year. That math works.

21:42.000 [CAMERA: Close-up, direct to camera]

RICHMOND: And if you're a business owner watching this thinking "I need this for my company" -- you do. Either build it yourself with what I showed you today, or hire someone who knows what they're doing. But do not wait, because your competitors are not waiting.


-- OUTRO ---------------------------------------------------------------

22:00.000 [CHAPTER: Full Walkthrough + Templates]
22:00.000 [CAMERA: Medium shot, Richmond at desk, relaxed]

RICHMOND: That's the full build. Voice agent from zero to production in 30 minutes. If you want to go deeper, I've got the full walkthrough with templates -- the exact prompt structure, the integration setup guides, and a client pitch deck you can customize. Link is in the description.

22:18.000 [TEXT ON-SCREEN: "Free templates + walkthrough -- link in description"]

RICHMOND: If this was useful, hit subscribe. I drop new content every week on how to build real businesses with AI -- not hype, not theory, systems that make money. I'll see you in the next one.

22:30.000 [CAMERA: Hold on Richmond for 2 seconds, then cut to end screen]
22:32.000 [VISUAL: End screen with subscribe button, next video suggestion, and link to templates]


-- SHORTS EXTRACTION POINTS -------------------------------------------

SHORT #1: "Voice Agent vs. Chatbot -- The Difference That Matters"

  LONG-FORM VERSION (01:48 - 03:44):
  The section explaining the three-layer architecture (ASR -> LLM -> TTS),
  the sub-800ms latency requirement, and why phone-based businesses need
  voice agents instead of chatbots.

  SHORT VERSION (reframed, self-contained):

  00:00.000 [CAMERA: Close-up, Richmond direct to camera]
  00:00.000 [TEXT ON-SCREEN: "This is NOT a chatbot"]

  RICHMOND: Stop calling AI voice agents "chatbots." They're not the same thing. A chatbot sits on your website and waits for someone to type. A voice agent picks up the phone, listens in real time, and responds in under a second. It uses speech recognition, an LLM to think, and text-to-speech to talk back -- all in under 800 milliseconds.

  00:18.000 [GRAPHIC: Quick pipeline animation: Voice -> ASR -> LLM -> TTS -> Voice, "<800ms"]

  RICHMOND: That's fast enough that callers don't even know it's AI. And for businesses that get leads by phone -- dentists, med spas, law firms -- this is the difference between a missed call and a booked appointment.

  00:34.000 [TEXT ON-SCREEN: "Missed call = lost revenue"]

  RICHMOND: This is just one piece of the full build. I walk through the entire setup -- from zero to working agent in 30 minutes -- in the full video.

  00:44.000 [TEXT ON-SCREEN: "Full video below"]

  ---

SHORT #2: "The Prompt Engineering Trick That Closes Objections"

  LONG-FORM VERSION (13:45 - 16:52):
  The three objection-handling patterns: pricing redirect, tentative booking
  for hesitators, and the callback-to-confirmation reframe.

  SHORT VERSION (reframed, self-contained):

  00:00.000 [CAMERA: Close-up, Richmond direct to camera]
  00:00.000 [TEXT ON-SCREEN: "Your AI voice agent is losing leads"]

  RICHMOND: Your AI voice agent is losing leads every time a caller says "how much does it cost?" and the agent freezes. Here's the fix. In your system prompt, write this: "If the caller asks about pricing, acknowledge the question, explain that pricing depends on their specific goals, and redirect to booking a free consultation."

  00:16.000 [TEXT ON-SCREEN: "Don't block. Redirect."]

  RICHMOND: The agent doesn't stonewall. It validates and redirects. Same principle for "I need to think about it" -- you engineer the prompt to offer a tentative hold on a time slot. You're not pressuring. You're reducing friction.

  00:30.000 [GRAPHIC: Quick comparison: "Bad: 'I can't help with pricing'" vs. "Good: 'Pricing depends on your goals -- let's book a quick consult'"]

  RICHMOND: Prompt engineering is what separates a demo from a money-making agent. I cover all three major objection patterns in the full video.

  00:44.000 [TEXT ON-SCREEN: "Full video below"]

  ---

SHORT #3: "The Real Cost: AI Voice Agent vs. Human Receptionist"

  LONG-FORM VERSION (19:30 - 20:28):
  The AI co-host's unit economics breakdown comparing human receptionist
  costs to AI voice agent costs.

  SHORT VERSION (reframed, self-contained):

  00:00.000 [CAMERA: Close-up, Richmond direct to camera]
  00:00.000 [TEXT ON-SCREEN: "$40,000 vs. $4,000"]

  RICHMOND: A human receptionist costs a business about $40,000 a year. That's before benefits, before training, before they call in sick, and they can't answer calls at 2 AM. An AI voice agent running 24/7 costs about $3,000 to $5,000 a year.

  00:14.000 [GRAPHIC: Animated bar chart -- Human: $40K, AI: $4K, with "24/7" label on AI bar]

  RICHMOND: It never misses a call. It never has a bad day. It books appointments, qualifies leads, and pushes everything to your CRM automatically. When you show a business owner that comparison, the question stops being "should I do this?" and becomes "how fast can you set it up?"

  00:32.000 [TEXT ON-SCREEN: "The question isn't IF -- it's HOW FAST"]

  RICHMOND: I break down three pricing models for selling this as a service -- including one where you only get paid per booked appointment. Full breakdown in the long-form video.

  00:45.000 [TEXT ON-SCREEN: "Full video below"]

  ---

SHORT #4: "How to Price AI Voice Agents as a Service"

  LONG-FORM VERSION (17:30 - 19:26):
  The three pricing models -- setup + retainer, per-minute, and
  performance-based.

  SHORT VERSION (reframed, self-contained):

  00:00.000 [CAMERA: Close-up, Richmond direct to camera]
  00:00.000 [TEXT ON-SCREEN: "What to charge for AI voice agents"]

  RICHMOND: Three pricing models for selling AI voice agents. One -- setup plus retainer. Charge $1,500 to $3,000 to build it, then $500 to $1,000 per month for optimization. Two -- per-minute. Charge clients 50 cents to a dollar per minute. Your cost is 7 to 15 cents. That's an 80 to 90 percent margin. Three -- per-booking. Charge $15 to $50 per appointment the agent books. Great for skeptical clients because you only get paid when it works.

  00:28.000 [GRAPHIC: Three cards appearing in sequence with each model's numbers]

  RICHMOND: Start with model one. It's predictable, it's profitable. Once you've got case studies, use model three to land bigger clients.

  00:38.000 [TEXT ON-SCREEN: "Start simple. Scale with proof."]

  RICHMOND: I go deep on all three models, plus the exact pitch I use with clients, in the full video.

  00:46.000 [TEXT ON-SCREEN: "Full video below"]


-- SCRIPT NOTES -------------------------------------------------------

CITATIONS TO VERIFY:

1. Gartner -- "$80 billion in agent labor cost reduction by 2026"
   Source: Gartner 2024 predictions for contact center AI
   Action: Pull exact report title and publication date from gartner.com

2. McKinsey -- "60-70% of routine customer service interactions automatable"
   Source: McKinsey Global Institute analysis on AI automation potential
   Action: Verify exact percentage and report name

3. Grand View Research -- "Conversational AI market $10-12B in 2023, 23-25% CAGR through 2030"
   Source: Grand View Research conversational AI market report
   Action: Pull exact figures and report date from grandviewresearch.com

4. Retell AI latency -- "Sub-800ms end-to-end response time"
   Source: retellai.com product documentation
   Action: Verify current latency claims on their docs/blog

5. Retell AI pricing -- "$0.07-0.12/min"
   Source: retellai.com/pricing
   Action: Check current pricing tiers before filming

6. Vapi pricing -- "$0.05/min base + LLM costs"
   Source: vapi.ai/pricing
   Action: Check current pricing before filming

7. Human receptionist salary -- "$35,000-$45,000/year"
   Source: Bureau of Labor Statistics, "Receptionists and Information Clerks"
   Action: Pull latest BLS median wage data

CONTENT SOURCE CREDIT:
- Manthan Patel's Retell AI content (YouTube) informed the agency/service pricing
  framing and GHL integration approach. Not directly cited in script but credit
  in video description recommended.

B-ROLL SOURCING SUGGESTIONS:
- Phone ringing / going to voicemail: stock footage (Pexels, Artgrid)
- Small business phone interaction: stock footage
- Business type montage (dental, auto, real estate, law): stock footage
- All screen recordings: capture live during Retell AI build session
- Voice samples: record directly from Retell AI voice library

PRODUCTION NOTES:
- Estimated runtime: 22-23 minutes
- Shorts count: 4 (each ~45 seconds)
- All test call audio should be captured live during recording session for authenticity
- Consider having a second person make the adversarial test calls so viewers
  see a real interaction, not Richmond talking to himself
- The prompt template shown on screen should also be available as a downloadable
  PDF in the description (matches the CTA)


DELIVERABLES CHECKLIST:

[x] Topic suitability assessment
[x] YouTube chapter titles + timestamps
[x] Full long-form script with Richmond and AI co-host dialogue
[x] All timestamps in MM:SS.ms format
[x] All visual cues (VISUAL, B-ROLL, GRAPHIC, CAMERA, TEXT ON-SCREEN) with timestamps
[x] 4 Short extraction points with long-form + reframed Short versions
[x] Verbal + visual CTAs in every Short driving back to long-form
[x] Script Notes with citations, B-roll sourcing, and production notes
```
