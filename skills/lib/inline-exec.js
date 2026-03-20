/**
 * Inline Command Execution Helper
 * 
 * Parses SKILL.md content and executes inline !`command` patterns.
 * 
 * Usage:
 *   const expanded = await expandInlineCommands(skillContent, execFunction)
 */

/**
 * Extract inline command patterns from text
 * @param {string} content - Skill content with !`command` patterns
 * @returns {Array<{match: string, command: string, start: number, end: number}>}
 */
function extractInlineCommands(content) {
  const pattern = /!\`([^`]+)\`/g
  const commands = []
  let match
  
  while ((match = pattern.exec(content)) !== null) {
    commands.push({
      match: match[0],           // Full match: !`command`
      command: match[1],         // Just the command
      start: match.index,
      end: match.index + match[0].length
    })
  }
  
  return commands
}

/**
 * Execute inline commands and replace with output
 * @param {string} content - Original content
 * @param {Function} execFn - Function that executes commands (async)
 * @returns {Promise<string>} - Content with commands replaced by output
 */
async function expandInlineCommands(content, execFn) {
  const commands = extractInlineCommands(content)
  
  if (commands.length === 0) {
    return content
  }
  
  // Execute all commands in parallel
  const results = await Promise.all(
    commands.map(async (cmd) => {
      try {
        const output = await execFn(cmd.command)
        return {
          ...cmd,
          output: output.trim() || '(no output)',
          error: null
        }
      } catch (error) {
        return {
          ...cmd,
          output: null,
          error: error.message
        }
      }
    })
  )
  
  // Replace commands with output (in reverse to preserve indices)
  let expanded = content
  for (let i = results.length - 1; i >= 0; i--) {
    const result = results[i]
    const replacement = result.error 
      ? `[ERROR: ${result.error}]`
      : result.output
    
    expanded = 
      expanded.slice(0, result.start) + 
      replacement + 
      expanded.slice(result.end)
  }
  
  return expanded
}

/**
 * Example usage pattern for OpenClaw skills
 */
async function exampleUsage() {
  // In your skill handler:
  const skillContent = `
    Current PR: !\`gh pr view --json number,title\`
    Files changed: !\`gh pr diff --name-only\`
  `
  
  // Define exec function (uses OpenClaw's exec tool)
  const execCommand = async (cmd) => {
    const result = await exec({ command: cmd })
    return result.stdout || result.output || ''
  }
  
  // Expand inline commands
  const expanded = await expandInlineCommands(skillContent, execCommand)
  
  // Now use expanded content with actual data
  console.log(expanded)
}

module.exports = {
  extractInlineCommands,
  expandInlineCommands
}
