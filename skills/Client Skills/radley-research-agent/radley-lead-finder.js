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
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

// ─── CONFIG ──────────────────────────────────────────────────────────────────

const DAYS_BACK = 7;
const TARGET_LEADS = 50;
const MIN_INTENT_SCORE = 5;
const SCORE_DELAY_MS = 250;
const FETCH_DELAY_MS = 1000;

// Keywords targeting US R&D tax credit pain points
const KEYWORDS = [
  'R&D tax credit',
  'research and development tax credit',
  'qualifying research expenses',
  'R&D documentation',
  'R&D tax software',
  'R&D payroll allocation',
  'section 41 credit',
  'R&D compliance startup',
  'R&D tax claim',
  'R&D audit risk',
  'R&D tax accountant',
  'engineering tax credits',
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

function extractTag(xml, tag) {
  const match = xml.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`, 'i'));
  return match ? match[1].trim() : '';
}

function extractAttr(xml, tag, attr) {
  const match = xml.match(new RegExp(`<${tag}[^>]*${attr}="([^"]*)"`, 'i'));
  return match ? match[1] : '';
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

function isRelevant(post) {
  const text = `${post.title} ${post.content}`.toLowerCase();
  return KEYWORDS.some((k) => text.includes(k.toLowerCase()));
}

// ─── REDDIT ──────────────────────────────────────────────────────────────────

function parseRedditRSS(xml, source) {
  const entries = [];
  const entryRegex = /<entry>([\s\S]*?)<\/entry>/g;
  let match;

  while ((match = entryRegex.exec(xml)) !== null) {
    const entry = match[1];
    const updated = extractTag(entry, 'updated');

    if (!isWithinWindow(updated)) continue;

    const rawAuthor = extractTag(entry, 'name') || extractTag(entry, 'author') || '';
    const author = stripHTML(rawAuthor).replace(/\/u\//i, '').trim();
    const content = stripHTML(extractTag(entry, 'content') || extractTag(entry, 'summary') || '');
    const title = stripHTML(extractTag(entry, 'title'));
    const link = extractAttr(entry, 'link', 'href') || extractTag(entry, 'link');

    entries.push({
      platform: 'Reddit',
      source,
      title,
      url: link,
      author,
      content: content.slice(0, 1200),
      date: updated,
      profileUrl: author ? `https://reddit.com/u/${author}` : '',
    });
  }

  return entries;
}

async function fetchRedditKeyword(keyword) {
  const encoded = encodeURIComponent(keyword);
  const url = `https://www.reddit.com/search.rss?q=${encoded}&sort=new&t=week&limit=25`;

  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'RadleyLeadFinder/1.0 (research automation)' },
    });
    if (!res.ok) return [];
    const xml = await res.text();
    return parseRedditRSS(xml, `search:${keyword}`);
  } catch (e) {
    console.error(`  Reddit keyword error "${keyword}": ${e.message}`);
    return [];
  }
}

async function fetchSubreddit(subreddit) {
  const url = `https://www.reddit.com/r/${subreddit}/new.rss?limit=50`;

  try {
    const res = await fetch(url, {
      headers: { 'User-Agent': 'RadleyLeadFinder/1.0 (research automation)' },
    });
    if (!res.ok) return [];
    const xml = await res.text();
    const posts = parseRedditRSS(xml, `r/${subreddit}`);
    // Only keep posts that mention R&D tax topics
    return posts.filter(isRelevant);
  } catch (e) {
    console.error(`  Subreddit error r/${subreddit}: ${e.message}`);
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
  const systemPrompt = `You are a GTM analyst for Radley (radley.tax), a US-focused SaaS platform that automates R&D tax credit claims. Radley connects to code repos, payroll systems, and project tools to auto-generate audit-ready R&D documentation for the IRS.

ICP (Ideal Customer Profile):
1. Founders and CTOs at US tech startups doing qualified research (software, hardware, biotech, medtech)
2. CFOs and finance teams managing R&D tax compliance and audit risk
3. Accountants and tax advisors who file R&D credit claims on behalf of clients

You must return ONLY a valid JSON object. No preamble, no markdown, no explanation.`;

  const userPrompt = `Evaluate this social post as a potential lead for Radley. Return ONLY this JSON:
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
    const response = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 400,
      system: systemPrompt,
      messages: [{ role: 'user', content: userPrompt }],
    });

    const text = response.content[0].text.replace(/```json|```/g, '').trim();
    return JSON.parse(text);
  } catch {
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

  // ── Reddit keyword search ─────────────────────────────────────────────────
  console.log('[1/3] Reddit keyword searches...');
  for (const keyword of KEYWORDS) {
    process.stdout.write(`  "${keyword}"...\n`);
    const posts = await fetchRedditKeyword(keyword);
    console.log(`        ${posts.length} posts found`);
    allPosts.push(...posts);
    await sleep(FETCH_DELAY_MS);
  }

  // ── Reddit subreddits ─────────────────────────────────────────────────────
  console.log('\n[2/3] Reddit subreddit feeds...');
  for (const sub of SUBREDDITS) {
    process.stdout.write(`  r/${sub}...\n`);
    const posts = await fetchSubreddit(sub);
    console.log(`        ${posts.length} relevant posts`);
    allPosts.push(...posts);
    await sleep(FETCH_DELAY_MS);
  }

  // ── Hacker News ───────────────────────────────────────────────────────────
  console.log('\n[3/3] Hacker News...');
  // Use top 6 keywords for HN — lower volume, higher signal
  for (const keyword of KEYWORDS.slice(0, 6)) {
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
