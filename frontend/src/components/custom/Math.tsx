import React, { useEffect, useRef } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface MathProps {
  latex: string;
  displayMode?: boolean;
  className?: string;
}

export const Math = React.memo<MathProps>(({ latex, displayMode = false, className = '' }) => {
  const containerRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      try {
        katex.render(latex, containerRef.current, {
          displayMode,
          throwOnError: false,
          errorColor: '#cc0000',
          strict: false,
        });
      } catch (error) {
        console.error('KaTeX rendering error:', error);
        if (containerRef.current) {
          containerRef.current.textContent = `[Math Error: ${latex}]`;
          containerRef.current.style.color = '#cc0000';
        }
      }
    }
  }, [latex, displayMode]);

  return (
    <span
      ref={containerRef}
      role="math"
      aria-label={latex}
      className={`katex-container ${className}`}
    />
  );
});

Math.displayName = 'Math';


interface MathContentProps {
  content: string;
}

/**
 * Component that parses message content for LaTeX and renders it with KaTeX.
 * Supports inline ($...$) and display ($$...$$) math modes.
 */
export const MathContent: React.FC<MathContentProps> = ({ content }) => {
  const parseLatex = (text: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let key = 0;

    // First, find display mode math ($$...$$)
    const displayRegex = /\$\$([\s\S]+?)\$\$/g;
    let match;

    // Collect all matches to process in order
    const allMatches: Array<{index: number, content: string, isDisplay: boolean}> = [];

    // Find display mode matches
    while ((match = displayRegex.exec(text)) !== null) {
      allMatches.push({
        index: match.index,
        content: match[1],
        isDisplay: true,
      });
    }

    // Find inline mode matches ($...$) but exclude display mode matches
    const inlineRegex = /\$([^$]+?)\$/g;
    while ((match = inlineRegex.exec(text)) !== null) {
      // Check if this match is inside a display mode match
      const isInsideDisplay = allMatches.some(
        (displayMatch) =>
          match.index >= displayMatch.index &&
          match.index < displayMatch.index + displayMatch.content.length + 4 // $$...$$ length
      );

      if (!isInsideDisplay) {
        allMatches.push({
          index: match.index,
          content: match[1],
          isDisplay: false,
        });
      }
    }

    // Sort matches by index
    allMatches.sort((a, b) => a.index - b.index);

    // Build the result
    allMatches.forEach((mathMatch) => {
      // Add text before this match
      if (mathMatch.index > lastIndex) {
        parts.push(
          <span key={`text-${key++}`}>
            {text.substring(lastIndex, mathMatch.index)}
          </span>
        );
      }

      // Add the math component
      parts.push(
        <Math
          key={`math-${key++}`}
          latex={mathMatch.content}
          displayMode={mathMatch.isDisplay}
        />
      );

      // Update last index
      lastIndex = mathMatch.index + mathMatch.content.length + (mathMatch.isDisplay ? 4 : 2);
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key={`text-${key++}`}>
          {text.substring(lastIndex)}
        </span>
      );
    }

    return parts.length > 0 ? parts : [<span key="text-0">{text}</span>];
  };

  return <>{parseLatex(content)}</>;
};
