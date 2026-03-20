# Compliance Reference: TCPA and CASL

This document covers the legal requirements for automated outbound calling in the US and Canada. Non-compliance can result in fines of $500–$1,500 per call (TCPA) or up to $10M CAD per violation (CASL). Take this seriously.

---

## TCPA (US — Telephone Consumer Protection Act)

### What it covers
- Automated or pre-recorded calls and texts to mobile numbers
- Calls to numbers on the National Do Not Call Registry
- Any artificial voice calls

### Key requirements

**1. Identification**
Every call must identify the caller by name and the company on whose behalf the call is made — within the first 30 seconds.

**2. Do Not Call compliance**
- Scrub your call list against the National DNC Registry before every campaign (updated monthly at donotcall.gov)
- Maintain your own internal suppression list for anyone who has requested no further contact
- Honor opt-out requests within 30 days (best practice: immediately)

**3. Calling hours**
- Calls are only permitted between 8am–9pm in the recipient's local time
- This implementation restricts to 9am–6pm as a conservative buffer

**4. Prior express consent for mobile numbers**
If using an auto-dialer or pre-recorded message to mobile numbers, you technically need prior express written consent. For purely AI-driven calls initiated in response to demonstrated buying intent (visitor de-anonymization), consult your legal counsel on whether this falls under the business relationship exception.

**5. Robocall rules**
If the call is fully automated (no live human available to take over), stricter rules apply. Ensure a human can intervene if needed — or at minimum, immediately honor a request to speak with a person.

### Safe harbor
The RISEN Framework targets people who have actively visited your site and shown purchase intent. This is strong signal of expressed interest, which strengthens your compliance position. Still, do not rely on this as a substitute for proper consent practices.

---

## CASL (Canada — Canadian Anti-Spam Legislation)

### What it covers
CASL primarily covers commercial electronic messages (email, SMS, social messages). For voice calls, the analogous regulation is the **CRTC's Unsolicited Telecommunications Rules**, but CASL principles apply to digital follow-ups (emails sent after the call).

### Key requirements for follow-up emails

**1. Identification**
Every commercial message must identify the sender clearly.

**2. Unsubscribe mechanism**
Every email must include a clear, functioning unsubscribe mechanism that works within 10 business days.

**3. Consent**
You must have either:
- **Express consent** (the person opted in explicitly), or
- **Implied consent** (they have a business relationship with you, or visited your site and provided their email)

Visiting your site alone may not constitute implied consent under CASL for email. Consult legal counsel before sending commercial emails to Canadian contacts who haven't provided a contact form submission or similar signal.

---

## Suppression List Management

### What goes on the list
- Anyone who says "don't call me" or "remove me from your list" or any variation
- Anyone who clicks unsubscribe in a follow-up email
- Numbers that return as disconnected or non-working
- Internal opt-outs from your sales team

### Implementation
Store the suppression list as a dedicated sheet in your Google Sheets CRM with these fields:
- Phone number (E.164 format, e.g., +12125550100)
- Email (if known)
- Company
- Date added
- Reason (DNC request / unsubscribe / disconnected / internal)

Before every call attempt, query this sheet (or cache it in memory) and abort if the number matches.

### Timing
Suppression list checks must happen at step 12 of the Sequence — after enrichment and timezone check, but before initiating the call. Never skip this check.

---

## Recommended legal review checklist

Before going live, have your legal counsel review:

- [ ] Whether your use of Apify/Apollo for lead data complies with their Terms of Service and applicable data protection laws (GDPR if you have EU visitors; CCPA for California contacts)
- [ ] Whether your telephony platform's recording features require two-party or one-party consent in the prospect's state (California, Florida, Pennsylvania, and others require two-party consent)
- [ ] Whether your value proposition and opening line accurately represent your product (FTC truth-in-advertising applies)
- [ ] Your data retention and deletion policy for call recordings and transcripts

---

## Quick reference: State-by-state recording consent (US)

| One-party consent (most states) | Two-party / all-party consent |
|--------------------------------|-------------------------------|
| Texas, New York, Georgia, etc. | California, Florida, Illinois, Maryland, Massachusetts, Michigan, Montana, Nevada, New Hampshire, Oregon, Pennsylvania, Washington |

For two-party consent states: begin the call with "This call may be recorded for quality and training purposes." This constitutes implied consent when the prospect continues the conversation.