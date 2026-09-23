/**
 * XSS-safe text and markdown utilities.
 * Ensures untrusted LLM synthesis and document text cannot execute arbitrary script injection,
 * and renders canonical citation tokens ([C1], [1], etc.) as interactive UI badges without HTML leakage.
 */

export function escapeHtml(unsafeText: string): string {
  return unsafeText
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Strips raw HTML tags from input string, normalizing any embedded citation tags
 * (e.g. `<span class="citation-badge" data-citation="cit-1">[1]</span>` -> `[1]`).
 */
export function stripRawHtmlAndNormalizeCitations(rawText: string): string {
  if (!rawText) return '';
  // 1. Convert any embedded HTML citation badges back to clean citation tokens e.g. [1] or [C1]
  let cleaned = rawText.replace(
    /<span[^>]*class=["'][^"']*citation-badge[^"']*["'][^>]*data-citation=["']([^"']+)["'][^>]*>(.*?)<\/span>/gi,
    (match, citId, inner) => {
      const token = inner?.trim() || `[${citId}]`;
      return token.startsWith('[') ? token : `[${token}]`;
    }
  );

  // 2. Strip any remaining raw HTML tags to prevent HTML leakage
  cleaned = cleaned.replace(/<\/?[a-z][a-z0-9]*\b[^>]*>/gi, '');

  return cleaned;
}

export function parseSafeMarkdown(content: string): string {
  if (!content) return '';

  // 1. Strip raw HTML and normalize legacy citation markup
  const cleaned = stripRawHtmlAndNormalizeCitations(content);

  // 2. Escape HTML entities for XSS safety
  let text = escapeHtml(cleaned);

  // 3. Bold (**text**)
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-white">$1</strong>');

  // 4. Italic (*text*)
  text = text.replace(/\*(.*?)\*/g, '<em class="italic text-carbon-200">$1</em>');

  // 5. Inline code (`code`)
  text = text.replace(
    /`([^`]+)`/g,
    '<code class="px-1.5 py-0.5 rounded bg-carbon-800 text-lime-300 font-mono text-xs border border-carbon-700">$1</code>'
  );

  // 6. Interactive Citation badges (e.g. [C1], [C2], [1], [2], [cit-1])
  text = text.replace(
    /\[([C\d]+|cit-[\w-]+)\]/g,
    '<span class="citation-badge inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono font-semibold bg-lime-400/10 text-lime-400 border border-lime-400/30 hover:bg-lime-400/20 hover:border-lime-400/60 shadow-sm mx-0.5 cursor-pointer transition-all active:scale-95" data-citation="$1">[$1]</span>'
  );

  // 7. Bullet lists
  text = text.replace(/^\s*[-*]\s+(.*)$/gm, '<li class="ml-4 list-disc text-carbon-300 leading-relaxed">$1</li>');

  // 8. Line breaks
  text = text.replace(/\n\n/g, '<br/><br/>').replace(/\n/g, '<br/>');

  return text;
}

