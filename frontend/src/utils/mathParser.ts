/**
 * Math Notation Parser - converts natural language math to LaTeX
 */

export function parseNaturalMathToLatex(input: string): string {
  let latex = input;

  // Word forms to LaTeX
  latex = latex.replace(/\b(\w+)\s+squared\b/gi, '$1^2');
  latex = latex.replace(/\b(\w+)\s+cubed\b/gi, '$1^3');
  latex = latex.replace(/\b(\w+)\s+to\s+the\s+power\s+of\s+(\d+)\b/gi, '$1^{$2}');

  // Roots
  latex = latex.replace(/\bsquare\s+root\s+of\s+([a-zA-Z0-9]+)\b/gi, '\\sqrt{$1}');
  latex = latex.replace(/\bcube\s+root\s+of\s+([a-zA-Z0-9]+)\b/gi, '\\sqrt[3]{$1}');
  latex = latex.replace(/\bsqrt\(([^)]+)\)/g, '\\sqrt{$1}');

  // Greek letters
  latex = latex.replace(/\bpi\b/gi, '\\pi');
  latex = latex.replace(/\btheta\b/gi, '\\theta');
  latex = latex.replace(/\balpha\b/gi, '\\alpha');
  latex = latex.replace(/\bbeta\b/gi, '\\beta');
  latex = latex.replace(/\bgamma\b/gi, '\\gamma');
  latex = latex.replace(/\bdelta\b/gi, '\\delta');
  latex = latex.replace(/\bepsilon\b/gi, '\\epsilon');
  latex = latex.replace(/\binfinity\b/gi, '\\infty');

  // Fractions (simple number fractions only to avoid false positives)
  latex = latex.replace(/\b(\d+)\s*\/\s*(\d+)\b/g, '\\frac{$1}{$2}');

  // Common operations
  latex = latex.replace(/\btimes\b/gi, '\\times');
  latex = latex.replace(/\bdivided by\b/gi, '\\div');

  return latex;
}

/**
 * Wraps content with LaTeX delimiters if not already present
 */
export function wrapWithLatexDelimiters(content: string, displayMode: boolean = false): string {
  if (displayMode) {
    return content.startsWith('$$') ? content : `$$${content}$$`;
  } else {
    return content.startsWith('$') && !content.startsWith('$$') ? content : `$${content}$`;
  }
}

/**
 * Checks if string contains LaTeX syntax
 */
export function containsLatex(str: string): boolean {
  return /\$.*\$|\\[a-zA-Z]+/.test(str);
}
