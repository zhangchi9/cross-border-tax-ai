// Utility functions for parsing AI messages

export interface MultipleChoiceOptions {
  options: string[];
  question: string;
}

/**
 * Detects if a message contains multiple choice options and extracts them
 */
export const extractMultipleChoiceOptions = (message: string): MultipleChoiceOptions | null => {
  console.log('Parsing message:', message);

  // Pattern 1: Options in parentheses - "What is your status? (US, Canada, or neither)"
  const parenthesesPattern = /([^?]+\?)\s*\(([^)]+)\)/i;
  const parenthesesMatch = message.match(parenthesesPattern);
  if (parenthesesMatch) {
    console.log('Found parentheses pattern:', parenthesesMatch);
    const optionsText = parenthesesMatch[2];

    // Split by commas and "or"
    const options = optionsText
      .split(/,|\bor\b/)
      .map(opt => opt.trim())
      .filter(opt => opt.length > 0 && opt.length < 50);

    if (options.length >= 2) {
      return {
        question: parenthesesMatch[1].trim(),
        options: options
      };
    }
  }

  // Pattern 2: Simple "or" questions - "US or Canada?"
  const orPattern = /([A-Za-z\s]+)\s+or\s+([A-Za-z\s]+)\?/i;
  const orMatch = message.match(orPattern);
  if (orMatch) {
    console.log('Found OR pattern:', orMatch);
    return {
      question: message.substring(0, orMatch.index! + orMatch[0].length),
      options: [orMatch[1].trim(), orMatch[2].trim()]
    };
  }

  // Pattern 3: Questions ending with colon followed by options
  const colonPattern = /([^?]+\?)\s*:?\s*([A-Za-z\s]+)\s+or\s+([A-Za-z\s]+)/i;
  const colonMatch = message.match(colonPattern);
  if (colonMatch) {
    console.log('Found colon pattern:', colonMatch);
    return {
      question: colonMatch[1].trim(),
      options: [colonMatch[2].trim(), colonMatch[3].trim()]
    };
  }

  // Pattern 4: "Are you:" followed by options
  const areYouPattern = /Are\s+you:\s*([^?]+)\s+or\s+([^?]+)/i;
  const areYouMatch = message.match(areYouPattern);
  if (areYouMatch) {
    console.log('Found Are you pattern:', areYouMatch);
    return {
      question: "Are you:",
      options: [areYouMatch[1].trim(), areYouMatch[2].trim()]
    };
  }

  // Pattern 5: Questions with "Which" followed by options
  const whichPattern = /Which\s+[^:?]+[:\?]\s*([^?]+)\s+or\s+([^?\.]+)/i;
  const whichMatch = message.match(whichPattern);
  if (whichMatch) {
    console.log('Found Which pattern:', whichMatch);
    const questionEnd = message.indexOf(whichMatch[0]) + whichMatch[0].length;
    return {
      question: message.substring(0, questionEnd),
      options: [whichMatch[1].trim(), whichMatch[2].trim()]
    };
  }

  console.log('No pattern matched');
  return null;
};