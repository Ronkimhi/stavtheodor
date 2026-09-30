#!/usr/bin/env python3
"""The fee gate shared by tools/check_pages.py and tools/check_variants.py (Ron, 2026-09-29).

Two rules, no more:
  1. Stav's fees are never stated: no dollar figure and no percentage that sits in a sentence about fees.
  2. No dollar figures in content pages and variants at all.
Research statistics stated as percentages stay allowed ("office workers were 32 percent more productive"),
because articles cite studies. A percentage fails only when a fee word is in the same sentence.

fee_violation(text) returns the offending text (a $ figure, or the percentage in a fee sentence) or None.
Self-test: python3 tools/fee_gate.py
"""
import re, sys

_ONES = r"(?:one|two|three|four|five|six|seven|eight|nine)"
_NUM = (r"(?:(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:[- ]" + _ONES + r")?|" + _ONES +
        r"|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|hundred)")
DOLLAR = re.compile(r"\$\s?\d|\d\s?dollars\b", re.I)
PERCENT = re.compile(r"\d[\d.,]*\s?(?:%|percent\b|per cent\b)|\b" + _NUM + r"(?:\s+(?:to|and)\s+" + _NUM + r")?\s+(?:percent|per cent)\b"
                     r"|\d+\s?אחוז|(?:עשר|עשרים|שלושים|ארבעים|חמישים|חמש|שלוש|ארבע)\S*\s+אחוז", re.I)
# fee words; "commission" only as a payment, not the verb ("commission a work", "we can commission")
FEE_WORD = re.compile(r"\b(?:fees?|retainers?|markups?|mark-ups?|charge[sd]?|charging|rates?|pricing|my fee|cost of my)\b"
                      r"|עמלה|עמלות|שכר טרחה|תעריף|מחירון", re.I)
COMMISSION = re.compile(r"(?<!\w)(\w+\s+)?commissions?(\s+\w+)?", re.I)
_VERB_BEFORE = {"to", "will", "can", "could", "would", "may", "might", "should", "we", "i", "you", "they", "who", "let"}
_VERB_AFTER = {"a", "an", "the", "new", "work", "works", "piece", "pieces", "artwork", "artworks", "original", "custom", "bespoke",
               "mural", "murals", "painting", "paintings", "portrait", "portraits", "sculpture", "artist", "artists", "him", "her",
               "them", "it", "one", "something", "photograph", "photographs"}
_BLOCK = re.compile(r"</?(?:p|li|ul|ol|h[1-6]|blockquote|figure|figcaption|br|div)\b[^>]*>", re.I)


def _commission_as_payment(sentence):
    for m in COMMISSION.finditer(sentence):
        before = (m.group(1) or "").strip().lower()
        after = (m.group(2) or "").strip().lower()
        if before not in _VERB_BEFORE and after not in _VERB_AFTER:
            return True
    return False


def sentences(text):
    """Plain sentences: block tags and newlines end one, inline tags vanish."""
    text = re.sub(r"<[^>]+>", "", _BLOCK.sub("\n", text))
    for line in text.split("\n"):
        for s in re.split(r"(?<=[.!?])\s+", line):
            if s.strip():
                yield s


def fee_violation(text):
    m = DOLLAR.search(text)
    if m:
        return m.group(0)
    for s in sentences(text):
        m = PERCENT.search(s)
        if m and (FEE_WORD.search(s) or _commission_as_payment(s)):
            return m.group(0)
    return None


def _selftest():
    ok = ["Office workers were 32 percent more productive.",
          "Studies found 12% of visitors stayed longer. Our fee is discussed on the call.",
          "We can commission a work for the lobby, and 40 percent of staff noticed it.",
          "<p>Artists</p><p>Ten to twenty percent of walls stay empty.</p>"]
    bad = ["Advisors charge a fee of ten to twenty percent.", "$5,000", "The commission is 15%.",
           "Her retainer runs 20 percent of the budget.", "About 5,000 dollars."]
    for t in ok:
        assert fee_violation(t) is None, ("should pass", t, fee_violation(t))
    for t in bad:
        assert fee_violation(t), ("should fail", t)
    print("fee_gate self-test: OK")


if __name__ == "__main__":
    _selftest()
