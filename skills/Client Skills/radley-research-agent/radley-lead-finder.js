#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────────────
// radley-lead-finder.js
// Social chatter lead finder for Radley (radley.tax)
//
// Sources (all free, no API keys required):
//   - Reddit RSS keyword search
//   - Reddit subreddit new post feeds (filtered for relevance)
//   - Hacker News via Algolia search API
//
// LinkedIn / Twitter / Facebook:
//   - Cannot be scraped freely. This script generates Google dork URLs
//     at the end. Open them manually or paste results back for scoring.
//
// Output: radley_leads.csv (50 qualified leads, sorted by intent score)
//
// Setup:
//   npm install @anthropic-ai/sdk
//   export ANTHROPIC_API_KEY=your_key
//   node radley-lead-finder.js
// ─────────────────────────────────────────────────────────────────────────────

import { writeFileSync } from 'fs';
import { spawnSync } from 'child_process';
import { platform } from 'os';

// Use claude CLI (Max subscription) — same approach as bishop/braincx agents
const CLAUDE_CMD = platform() === 'win32'
  ? 'C:/Users/richm/AppData/Roaming/npm/claude.cmd'
  : 'claude';

// ─── CONFIG ──────────────────────────────────────────────────────────────────

const DAYS_BACK = 365;
const TARGET_LEADS = 50;
const MIN_INTENT_SCORE = 4;
const SCORE_DELAY_MS = 250;
const FETCH_DELAY_MS = 1500;

// High-signal keywords — specific enough to return on-topic posts
const KEYWORDS = [
  'R&D tax credit',
  'research and development tax credit',
  'qualified research expenses',
  'section 41 credit',
  'R&D documentation',
  'R&D payroll credit',
  'R&D tax software',
  'R&D audit',
  'R&D tax accountant',
  'qualifying research activities',
  'payroll tax offset startup credit',
  'startup R&D credit',
  'biotech R&D tax',
  'engineering tax credit',
  'R&D compliance',
  'R&D wage allocation',
];

// Subreddits where founders, CFOs, and tax pros hang out
const SUBREDDITS = [
  'taxpros',
  'smallbusiness',
  'startups',
  'Entrepreneur',
  'accounting',
  'tax',
  'SaaS',
  'techstartups',
  'CFO',
  'fintech',
  'YCombinator',
  'CPA',
  'Bookkeeping',
  'venturecapital',
  'biotech',
  'hardware',
  'medtech',
  'AskAccountants',
  'personalfinance',
  'BusinessTax',
  'legaladvice',
  'consulting',
  'LifeofaCPA',
  'investing',
];

// Google dork templates for manual LinkedIn/Twitter/Facebook searching
const MANUAL_DORKS = [
  `site:linkedin.com/posts "R&D tax credit" startup`,
  `site:linkedin.com/posts "qualifying research expenses"`,
  `site:linkedin.com/posts "R&D documentation" pain`,
  `site:twitter.com "R&D tax credit" -is:retweet startup`,
  `site:twitter.com "R&D tax software" OR "R&D compliance"`,
  `site:facebook.com/groups "R&D tax credit" help`,
  `site:facebook.com/groups "research and development tax" startup`,
  `site:reddit.com "R&D tax credit" "anyone else" OR "frustrated" OR "nightmare"`,
  `"R&D tax credit" "software company" (help OR advice OR recommend) site:quora.com`,
];

// ─── UTILITIES ───────────────────────────────────────────────────────────────

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d;
}

function isWithinWindow(dateStr) {
  if (!dateStr) return false;
  return new Date(dateStr) >= daysAgo(DAYS_BACK);
}

function stripHTML(str) {
  return str
    .replace(/<[^>]+>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function dedup(items) {
  const seen = new Set();
  return items.filter((item) => {
    const key = item.url || `${item.author}-${item.title}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

const RELEVANCE_TERMS = [
  // Exact product terms
  'r&d tax', 'r&d credit', 'r&d documentation', 'r&d audit', 'r&d compliance',
  'research tax credit', 'research and development tax', 'research credit',
  'qualified research', 'qualifying research', 'qualifying activities',
  'research expenses', 'research activities',
  // Section references
  'section 41', 'sec. 41', 'sec 41', '§41', 'irc 41', 'irc §41',
  // Adjacent terms
  'payroll tax offset', 'startup tax credit', 'engineering tax credit',
  'software tax credit', 'biotech tax', 'innovation credit',
  // Short forms people actually use
  ' r&d ', 'r&d,', 'r&d.', 'r&d:', '(r&d)', 'rd tax', 'rdec',
  // Credit study language
  'credit study', 'nexus fraction', 'wages allocation', 'qre ',
  // Tool/process pain
  'r&d software', 'r&d tool', 'r&d documentation burden',
];

function isRelevant(post) {
  const text = ` ${post.title} ${post.content} `.toLowerCase();
  return RELEVANCE_TERMS.some((k) => text.includes(k.toLowerCase()));
}

// High-signal subreddits: skip isRelevant, let Claude judge everything
const HIGH_SIGNAL_SUBS = new Set(['taxpros', 'accounting', 'tax', 'AskAccountants', 'LifeofaCPA', 'CPA']);

// ─── REDDIT (JSON API) ───────────────────────────────────────────────────────

const REDDIT_HEADERS = {
  'User-Agent': 'RadleyLeadFinder/1.0 (research bot; contact radley.tax)',
  'Accept': 'application/json',
};

function parseRedditPost(child, source) {
  const d = child.data;
  const created = new Date(d.created_utc * 1000).toISOString();
  if (!isWithinWindow(created)) return null;

  const content = stripHTML(d.selftext || d.body || '').slice(0, 1200);
  const title = d.title || d.link_title || '';
  const author = d.author || '';
  const url = d.url?.startsWith('http') ? d.url : `https://reddit.com${d.permalink}`;

  return {
    platform: 'Reddit',
    source,
    title,
    url: `https://reddit.com${d.permalink}`,
    author,
    content: `${title} ${content}`.trim(),
    date: created,
    profileUrl: author ? `https://reddit.com/u/${author}` : '',
  };
}

async function fetchRedditKeyword(keyword) {
  // No quotes — let Reddit's full-text search surface broader matches
  const encoded = encodeURIComponent(keyword);
  const url = `https://www.reddit.com/search.json?q=${encoded}&sort=new&t=year&limit=100&type=link,self`;

  try {
    const res = await fetch(url, { headers: REDDIT_HEADERS });
    if (!res.ok) return [];
    const data = await res.json();
    return (data?.data?.children || [])
      .map(c => parseRedditPost(c, `search:${keyword}`))
      .filter(Boolean)
      .filter(isRelevant);
  } catch (e) {
    console.error(`  Reddit keyword error "${keyword}": ${e.message}`);
    return [];
  }
}

async function fetchRedditComments(keyword) {
  // Search comments — this surfaces discussions buried in threads
  const encoded = encodeURIComponent(keyword);
  const url = `https://www.reddit.com/search.json?q=${encoded}&sort=new&t=year&limit=100&type=comment`;

  try {
    const res = await fetch(url, { headers: REDDIT_HEADERS });
    if (!res.ok) return [];
    const data = await res.json();
    return (data?.data?.children || [])
      .map(c => parseRedditPost(c, `comment:${keyword}`))
      .filter(Boolean)
      .filter(isRelevant);
  } catch (e) {
    console.error(`  Reddit comment error "${keyword}": ${e.message}`);
    return [];
  }
}

async function fetchSubreddit(subreddit) {
  // Pull /new feed directly — avoids Reddit's broken search for niche terms
  // High-signal subs (taxpros, accounting, tax): pass all posts to Claude
  // Other subs: pre-filter with isRelevant to avoid noise
  const url = `https://www.reddit.com/r/${subreddit}/new.json?limit=100`;

  try {
    const res = await fetch(url, { headers: REDDIT_HEADERS });
    if (!res.ok) return [];
    const data = await res.json();
    const posts = (data?.data?.children || [])
      .map(c => parseRedditPost(c, `r/${subreddit}`))
      .filter(Boolean);
    return HIGH_SIGNAL_SUBS.has(subreddit) ? posts : posts.filter(isRelevant);
  } catch (e) {
    console.error(`  Subreddit error r/${subreddit}: ${e.message}`);
    return [];
  }
}

async function fetchSubredditSearch(subreddit, query) {
  // Targeted search within a subreddit for high-signal subs
  const q = encodeURIComponent(query);
  const url = `https://www.reddit.com/r/${subreddit}/search.json?q=${q}&restrict_sr=true&sort=relevance&t=year&limit=100`;

  try {
    const res = await fetch(url, { headers: REDDIT_HEADERS });
    if (!res.ok) return [];
    const data = await res.json();
    return (data?.data?.children || [])
      .map(c => parseRedditPost(c, `r/${subreddit}:search`))
      .filter(Boolean)
      .filter(isRelevant);
  } catch (e) {
    return [];
  }
}

// ─── HACKER NEWS ─────────────────────────────────────────────────────────────

async function fetchHackerNews(keyword) {
  const cutoff = Math.floor(daysAgo(DAYS_BACK).getTime() / 1000);
  const encoded = encodeURIComponent(keyword);
  const url = `https://hn.algolia.com/api/v1/search?query=${encoded}&tags=(story,comment)&numericFilters=created_at_i>${cutoff}&hitsPerPage=30`;

  try {
    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();

    return data.hits.map((hit) => ({
      platform: 'Hacker News',
      source: 'HN Algolia',
      title: stripHTML(hit.title || hit.comment_text?.slice(0, 100) || ''),
      url: hit.url || `https://news.ycombinator.com/item?id=${hit.objectID}`,
      author: hit.author || '',
      content: stripHTML(hit.comment_text || hit.story_text || '').slice(0, 1200),
      date: hit.created_at,
      profileUrl: hit.author ? `https://news.ycombinator.com/user?id=${hit.author}` : '',
    }));
  } catch (e) {
    console.error(`  HN error "${keyword}": ${e.message}`);
    return [];
  }
}

// ─── CLAUDE SCORING ──────────────────────────────────────────────────────────

async function scoreLead(post) {
  const prompt = `You are a GTM analyst for Radley (radley.tax), a US-focused SaaS platform that automates R&D tax credit claims. Radley connects to code repos, payroll systems, and project tools to auto-generate audit-ready R&D documentation for the IRS.

ICP (Ideal Customer Profile):
1. Founders and CTOs at US tech startups doing qualified research (software, hardware, biotech, medtech)
2. CFOs and finance teams managing R&D tax compliance and audit risk
3. Accountants and tax advisors who file R&D credit claims on behalf of clients

Evaluate this social post as a potential lead for Radley. Return ONLY a valid JSON object — no preamble, no markdown, no explanation:
{
  "isLead": true or false,
  "intentScore": integer 1-10 (10 = actively seeking R&D tax solution, 1 = irrelevant),
  "buyerPersona": "Founder/CTO" | "CFO/Finance" | "Accountant/Advisor" | "Unknown",
  "inferredRole": "their likely job title or null",
  "inferredCompany": "company name if mentioned or null",
  "painSignal": "one sentence describing their exact pain point",
  "outreachAngle": "one sentence on how Radley should approach this person",
  "contactHint": "any visible contact info (email, LinkedIn URL, Twitter handle) or null"
}

Scoring guide:
9-10: Actively asking for R&D tax tool / complaining about documentation burden
7-8: Discussing R&D tax pain or asking for advisor recommendations
5-6: In the ICP, mentions R&D work, might be receptive
1-4: Not relevant or not in ICP

Platform: ${post.platform}
Date: ${post.date}
Author: ${post.author}
Title: ${post.title}
Content: ${post.content}`;

  try {
    const proc = spawnSync(
      CLAUDE_CMD,
      ['--print', '--model', 'sonnet', '--max-turns', '1'],
      { input: prompt, encoding: 'utf8', timeout: 60000, shell: true }
    );
    if (proc.status !== 0) throw new Error(`CLI exit ${proc.status}: ${proc.stderr?.slice(0, 200)}`);
    const text = proc.stdout.replace(/```json|```/g, '').trim();
    const parsed = JSON.parse(text);
    return parsed;
  } catch (e) {
    process.stderr.write(`  [score-err] ${e.message}\n`);
    return {
      isLead: false,
      intentScore: 0,
      buyerPersona: 'Unknown',
      inferredRole: null,
      inferredCompany: null,
      painSignal: '',
      outreachAngle: '',
      contactHint: null,
    };
  }
}

// ─── CSV OUTPUT ───────────────────────────────────────────────────────────────

function escapeCSV(val) {
  return `"${String(val ?? '').replace(/"/g, '""')}"`;
}

function toCSV(leads) {
  const headers = [
    'Rank',
    'Intent Score',
    'Platform',
    'Buyer Persona',
    'Inferred Role',
    'Company',
    'Author / Handle',
    'Profile URL',
    'Post URL',
    'Date Posted',
    'Pain Signal',
    'Outreach Angle',
    'Contact Hint',
    'Post Title',
  ];

  const rows = leads.map((l, i) => [
    i + 1,
    l.score?.intentScore ?? '',
    l.platform,
    l.score?.buyerPersona ?? '',
    l.score?.inferredRole ?? '',
    l.score?.inferredCompany ?? '',
    l.author,
    l.profileUrl,
    l.url,
    new Date(l.date).toLocaleDateString('en-US'),
    l.score?.painSignal ?? '',
    l.score?.outreachAngle ?? '',
    l.score?.contactHint ?? '',
    l.title,
  ].map(escapeCSV));

  return [headers.map(escapeCSV).join(','), ...rows.map((r) => r.join(','))].join('\n');
}

// ─── MAIN ────────────────────────────────────────────────────────────────────

async function main() {
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  Radley Lead Finder');
  console.log(`  Looking back: ${DAYS_BACK} days`);
  console.log(`  Target leads: ${TARGET_LEADS}`);
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  let allPosts = [];

  // ── Reddit keyword search (posts) ────────────────────────────────────────
  console.log('[1/4] Reddit keyword searches (posts)...');
  for (const keyword of KEYWORDS) {
    process.stdout.write(`  "${keyword}"...\n`);
    const posts = await fetchRedditKeyword(keyword);
    console.log(`        ${posts.length} posts found`);
    allPosts.push(...posts);
    await sleep(FETCH_DELAY_MS);
  }

  // ── Reddit keyword search (comments) ─────────────────────────────────────
  // Top 8 highest-intent keywords — comment threads surface real pain
  const COMMENT_KEYWORDS = KEYWORDS.slice(0, 8);
  console.log('\n[2/4] Reddit comment searches...');
  for (const keyword of COMMENT_KEYWORDS) {
    process.stdout.write(`  "${keyword}"...\n`);
    const posts = await fetchRedditComments(keyword);
    console.log(`        ${posts.length} comments found`);
    allPosts.push(...posts);
    await sleep(FETCH_DELAY_MS);
  }

  // ── Reddit subreddits (new feed, locally filtered) ────────────────────────
  console.log('\n[3/4] Reddit subreddit feeds...');
  for (const sub of SUBREDDITS) {
    process.stdout.write(`  r/${sub}...\n`);
    const posts = await fetchSubreddit(sub);
    console.log(`        ${posts.length} relevant posts`);
    allPosts.push(...posts);
    await sleep(FETCH_DELAY_MS);
  }

  // ── Targeted search on highest-signal subs ────────────────────────────────
  const HIGH_SIGNAL_SUBS = ['taxpros', 'accounting', 'tax', 'smallbusiness', 'startups', 'Entrepreneur', 'SaaS'];
  const TARGETED_QUERIES = ['R&D tax credit', 'research tax credit', 'qualified research', 'section 41'];
  console.log('\n  [bonus] Targeted searches on high-signal subs...');
  for (const sub of HIGH_SIGNAL_SUBS) {
    for (const q of TARGETED_QUERIES) {
      const posts = await fetchSubredditSearch(sub, q);
      if (posts.length) console.log(`    r/${sub} "${q}": ${posts.length}`);
      allPosts.push(...posts);
      await sleep(800);
    }
  }

  // ── Hacker News ───────────────────────────────────────────────────────────
  console.log('\n[4/4] Hacker News...');
  for (const keyword of KEYWORDS.slice(0, 8)) {
    process.stdout.write(`  "${keyword}"...\n`);
    const posts = await fetchHackerNews(keyword);
    console.log(`        ${posts.length} posts found`);
    allPosts.push(...posts);
    await sleep(500);
  }

  // ── Dedup and report ─────────────────────────────────────────────────────
  allPosts = dedup(allPosts);
  console.log(`\nTotal unique posts to score: ${allPosts.length}`);

  if (allPosts.length === 0) {
    console.log('\nNo posts found. This can happen if Reddit rate-limits the RSS feed.');
    console.log('Try running again in a few minutes or reduce KEYWORDS count.');
    process.exit(0);
  }

  // ── Score with Claude ─────────────────────────────────────────────────────
  console.log('\nScoring with Claude...\n');
  const qualifiedLeads = [];
  let scored = 0;

  for (const post of allPosts) {
    scored++;
    const pct = Math.round((scored / allPosts.length) * 100);
    process.stdout.write(
      `  [${pct}%] Scoring ${scored}/${allPosts.length} | Qualified: ${qualifiedLeads.length}/${TARGET_LEADS}\r`
    );

    const score = await scoreLead(post);

    if (score.isLead && score.intentScore >= MIN_INTENT_SCORE) {
      qualifiedLeads.push({ ...post, score });
    }

    await sleep(SCORE_DELAY_MS);

    if (qualifiedLeads.length >= TARGET_LEADS) break;
  }

  console.log('\n');

  // ── Sort and write CSV ────────────────────────────────────────────────────
  qualifiedLeads.sort((a, b) => (b.score?.intentScore ?? 0) - (a.score?.intentScore ?? 0));
  const top50 = qualifiedLeads.slice(0, TARGET_LEADS);

  const csv = toCSV(top50);
  writeFileSync('radley_leads.csv', csv);

  // ── Summary ───────────────────────────────────────────────────────────────
  const avgScore =
    top50.length > 0
      ? (top50.reduce((s, l) => s + (l.score?.intentScore ?? 0), 0) / top50.length).toFixed(1)
      : 0;

  const byPersona = top50.reduce((acc, l) => {
    const p = l.score?.buyerPersona || 'Unknown';
    acc[p] = (acc[p] || 0) + 1;
    return acc;
  }, {});

  const byPlatform = top50.reduce((acc, l) => {
    acc[l.platform] = (acc[l.platform] || 0) + 1;
    return acc;
  }, {});

  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`  Leads found:       ${top50.length}`);
  console.log(`  Avg intent score:  ${avgScore}/10`);
  console.log('\n  By persona:');
  Object.entries(byPersona).forEach(([k, v]) => console.log(`    ${k}: ${v}`));
  console.log('\n  By platform:');
  Object.entries(byPlatform).forEach(([k, v]) => console.log(`    ${k}: ${v}`));
  console.log('\n  Output: radley_leads.csv');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

  // ── Manual Google dork URLs ───────────────────────────────────────────────
  console.log('\n Manual searches for LinkedIn / Twitter / Facebook');
  console.log('  Open these in your browser (add results to leads manually):\n');
  MANUAL_DORKS.forEach((q) => {
    console.log(`  https://www.google.com/search?q=${encodeURIComponent(q)}&tbs=qdr:w`);
    console.log();
  });
  console.log(`  Note: &tbs=qdr:w filters Google results to the past week.`);
}

main().catch((err) => {
  console.error('\nFatal error:', err.message);
  process.exit(1);
});
